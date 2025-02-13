from fastapi import FastAPI, File, UploadFile, Form
import subprocess
import os
import distro

app = FastAPI()

# ------------------ 辅助函数 ------------------

def run_script(mode: str):
    """
    执行 `/home/{mode}/stop.sh` 脚本
    """
    script_path = f"/home/{mode}/stop.sh"
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        try:
            subprocess.run([script_path], shell=True, check=True)
            print(f"执行脚本 {script_path} 成功")
        except subprocess.CalledProcessError as e:
            print(f"执行脚本 {script_path} 失败: {e}")
    else:
        print(f"脚本 {script_path} 不存在或无执行权限")
        
def mask_to_cidr(netmask: str) -> int:
    """
    将子网掩码(如 '255.255.255.0')转换为CIDR表示(如 24)。
    """
    return sum(bin(int(octet)).count("1") for octet in netmask.split("."))


def update_config(path: str, updates: dict):
    """
    打开指定配置文件，将 updates 字典中的 key=value
    更新/追加到文件中（过滤掉空值）。
    """
    if not os.path.exists(path):
        lines = []
    else:
        with open(path, "r") as f:
            lines = f.readlines()

    # 过滤空值或空白字符串
    updates = {k: v.strip() for k, v in updates.items() if v and v.strip()}

    for key, new_value in updates.items():
        found = False
        for i in range(len(lines)):
            if lines[i].startswith(f"{key}: "):
                lines[i] = f"{key}: {new_value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}: {new_value}\n")

    # 只有在有有效更新的情况下才写入
    if updates:
        with open(path, "w") as f:
            f.writelines(lines)

# 将“风电”（wind）或“电梯”（elevator）映射到文件路径
def get_config_path(mode: str) -> str:
    """
    根据前端传入的 mode(如 'wind' or 'elevator')，
    构造对应的配置文件路径。
    例如: /home/wind/conf/config or /home/elevator/conf/config
    """
    return f"/home/{mode}/conf/config"


@app.post("/change-ip")
def change_ip(
    new_ip: str = Form(""),
    subnet_mask: str = Form(""),
    gateway: str = Form(""),
    dns1: str = Form(""),
    dns2: str = Form("")
):
    # 收集要修改的项目
    ip_cidr = None
    print(new_ip, subnet_mask, gateway, dns1, dns2)
    if new_ip and subnet_mask:
        cidr = mask_to_cidr(subnet_mask)
        ip_cidr = f"{new_ip}/{cidr}"

    dns_list = [dns for dns in (dns1, dns2) if dns]  # 过滤空字符串

    # 如果所有字段都空，则直接跳过
    if not (ip_cidr or gateway or dns_list):
        return {
            "status": "skipped",
            "message": "No valid parameters to update. Skipped all changes."
        }

    dist_id = distro.id().lower()
    # ---- Ubuntu / Debian: 使用 netplan ----
    if dist_id in ["ubuntu", "debian"]:
        try:
            # 构建 netplan 配置文件内容
            netplan_conf = [
                "network:",
                "  version: 2",
                "  renderer: networkd",
                "  ethernets:",
                "    enp1s0:"
            ]

            # 只有在 new_ip+subnet_mask 都有时才写 addresses
            if ip_cidr:
                netplan_conf.append(f"      addresses:")
                netplan_conf.append(f"        - {ip_cidr}")

            # 如果有 gateway
            if gateway:
                netplan_conf.append(f"      gateway4: {gateway}")

            # 如果有 dns
            if dns_list:
                dns_str = ", ".join(dns_list)
                netplan_conf.append("      nameservers:")
                netplan_conf.append(f"        addresses: [{dns_str}]")

            # 拼成完整 YAML
            final_yaml = "\n".join(netplan_conf) + "\n"

            # 写入自定义文件
            with open("/etc/netplan/01-custom.yaml", "w") as f:
                f.write(final_yaml)

            # 应用 netplan
            subprocess.run(["sudo", "netplan", "apply"], check=True)

            return {
                "status": "success",
                "message": f"Ubuntu/Debian netplan updated: IP={ip_cidr}, GW={gateway}, DNS={dns_list}"
            }
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": str(e)}

    # ---- CentOS / RHEL / Fedora: 使用 nmcli ----
    else:
        # 构建 nmcli 命令行参数
        nmcli_cmds = []
        if ip_cidr:
            nmcli_cmds += ["ipv4.addresses", ip_cidr, "ipv4.method", "manual"]
        if gateway:
            nmcli_cmds += ["ipv4.gateway", gateway]
        if dns_list:
            nmcli_cmds += ["ipv4.dns", ",".join(dns_list)]

        try:
            subprocess.run(["sudo", "nmcli", "con", "mod", "enp1s0"] + nmcli_cmds, check=True)
            subprocess.run(["sudo", "nmcli", "con", "up", "enp1s0"], check=True)

            return {
                "status": "success",
                "message": f"CentOS/RHEL/Fedora nmcli updated: IP={ip_cidr}, GW={gateway}, DNS={dns_list}"
            }
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": str(e)}

@app.post("/upload-file")
def upload_file(file: UploadFile = File(...), target_path: str = Form(...)):
    """ 通用示例：上传文件并覆盖指定路径 """
    try:
        with open(target_path, "wb") as f:
            f.write(file.file.read())
        return {"status": "success", "message": f"文件上传到 {target_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/change-mqtt")
def change_mqtt(
    mode: str = Form(...),
    mqtt_address: str = Form(""),
    mqtt_username: str = Form(""),
    mqtt_password: str = Form("")
):
    """
    修改 MQTT 配置
    - mode: 'wind' (对应 风电) 或 'elevator' (对应 电梯)
    - mqtt_address: 要写入的 mqtt_address
    - mqtt_username: 要写入的 mqtt_username
    - mqtt_password: 要写入的 mqtt_password
    """
    config_path = get_config_path(mode)
    try:
        update_config(config_path, {
            "mqtt_address": mqtt_address,
            "mqtt_username": mqtt_username,
            "mqtt_password": mqtt_password
        })
        run_script(mode)
        return {"status": "success", "message": f"已修改 {config_path} 中的 MQTT 配置"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/change-backend")
def change_backend(
    mode: str = Form(...),
    backend_url: str = Form(""),
    backend_port: str = Form("")
):
    """
    修改后端地址
    - mode: 'wind' 或 'elevator'
    - backend_url: 要写入的 backend_ip
    - backend_port: 要写入的 backend_port
    """
    config_path = get_config_path(mode)
    try:
        update_config(config_path, {
            "backend_ip": backend_url,
            "backend_port": backend_port
        })
        run_script(mode)
        return {"status": "success", "message": f"已修改 {config_path} 中的后端配置"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/change-interval")
def change_interval(
    mode: str = Form(...),
    interval: int = Form(...)
):
    """
    修改上传周期(package_freq)
    - mode: 'wind' 或 'elevator'
    - interval: 传入的周期，必须 >= 5
    """
    if interval < 5:
        return {"status": "error", "message": "上传周期必须 >= 5"}

    config_path = get_config_path(mode)
    try:
        update_config(config_path, {
            "package_freq": str(interval)
        })
        run_script(mode)
        return {"status": "success", "message": f"已修改 {config_path} 中的上传周期为 {interval}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
