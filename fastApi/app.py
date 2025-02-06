from fastapi import FastAPI, File, UploadFile, Form
import subprocess
import os

app = FastAPI()

# ------------------ 辅助函数 ------------------

def update_config(path: str, updates: dict):
    """
    打开指定配置文件，将 updates 字典中的 key=value
    更新/追加到文件中。
    
    - path: 配置文件完整路径
    - updates: { "mqtt_address": "xxx", "backend_ip": "yyy", ... }
    """
    if not os.path.exists(path):
        # 如果文件不存在，直接创建写入
        lines = []
    else:
        with open(path, "r") as f:
            lines = f.readlines()

    # 对 updates 中的每个 key，找到对应行并更新；如不存在，则追加。
    for key, new_value in updates.items():
        found = False
        for i in range(len(lines)):
            if lines[i].startswith(f"{key}: "):
                lines[i] = f"{key}: {new_value}\n"
                found = True
                break
        if not found:
            # 如果未在文件中找到该 key，追加一行
            lines.append(f"{key}: {new_value}\n")

    # 写回文件
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

# ------------------ 原有接口 ------------------

@app.post("/change-ip")
def change_ip(new_ip: str = Form(...)):
    """ 修改本机 IP 地址（需要 root 权限） """
    try:
        subprocess.run(["sudo", "ip", "addr", "add", new_ip, "dev", "eth0"], check=True)
        return {"status": "success", "message": f"IP changed to {new_ip}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

@app.post("/modify-file")
def modify_file(file_path: str = Form(...), line_number: int = Form(...), new_content: str = Form(...)):
    """ 通用示例：修改指定文件某一行内容（行号从1开始） """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        if line_number < 1 or line_number > len(lines):
            return {"status": "error", "message": "行号超出范围"}

        lines[line_number - 1] = new_content + "\n"

        with open(file_path, "w") as f:
            f.writelines(lines)

        return {"status": "success", "message": f"文件 {file_path} 第 {line_number} 行已修改"}
    except Exception as e:
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

# ------------------ 新增接口 ------------------

@app.post("/change-mqtt")
def change_mqtt(
    mode: str = Form(...),
    mqtt_address: str = Form(...),
    mqtt_username: str = Form(...),
    mqtt_password: str = Form(...)
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
        return {"status": "success", "message": f"已修改 {config_path} 中的 MQTT 配置"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/change-backend")
def change_backend(
    mode: str = Form(...),
    backend_url: str = Form(...),
    backend_port: str = Form(...)
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
        return {"status": "success", "message": f"已修改 {config_path} 中的上传周期为 {interval}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
