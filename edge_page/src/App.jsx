import { useState } from "react";

export default function App() {
  // 选择模式：风电(wind) or 电梯(elevator)
  const [mode, setMode] = useState("elevator"); 

  // 修改 IP 相关信息
  const [ip, setIp] = useState("");
  const [subnetMask, setSubnetMask] = useState("255.255.255.0");
  const [gateway, setGateway] = useState("");
  const [dns1, setDns1] = useState("");
  const [dns2, setDns2] = useState("");

  // 修改 MQTT
  const [mqttAddress, setMqttAddress] = useState("");
  const [mqttUsername, setMqttUsername] = useState("");
  const [mqttPassword, setMqttPassword] = useState("");

  // 修改后端地址
  const [backendUrl, setBackendUrl] = useState("");
  const [backendPort, setBackendPort] = useState("");

  // 修改上传周期（>= 5）
  const [uploadInterval, setUploadInterval] = useState(5);

  // 上传模型（文件）
  const [modelFile, setModelFile] = useState(null);

  // ------------------- 事件处理函数 -------------------

  // 1. 修改 IP
  const changeIP = async () => {
    // 如果 IP 有值，但子网掩码为空，或子网掩码有值但 IP 为空，就提示错误并退出
    if ((ip && !subnetMask) || (!ip && subnetMask)) {
      alert("IP 和子网掩码必须同时设置，或者同时留空。");
      return;
    }
  
    // 构造请求参数
    const params = new URLSearchParams({
      new_ip: ip,
      subnet_mask: subnetMask,
      gateway: gateway,
      dns1: dns1,
      dns2: dns2,
    });
  
    await fetch("/change-ip", {
      method: "POST",
      body: params,
    });
  };

  // 2. 修改 MQTT
  const changeMQTT = async () => {
    const params = new URLSearchParams({
      mode,                   // wind / elevator
      mqtt_address: mqttAddress,
      mqtt_username: mqttUsername,
      mqtt_password: mqttPassword,
    });

    await fetch("/change-mqtt", {
      method: "POST",
      body: params,
    });
  };

  // 3. 修改后端地址
  const changeBackend = async () => {
    const params = new URLSearchParams({
      mode,                    // wind / elevator
      backend_url: backendUrl,
      backend_port: backendPort,
    });

    await fetch("/change-backend", {
      method: "POST",
      body: params,
    });
  };

  // 4. 修改上传周期
  const changeInterval = async () => {
    // 前端简单校验
    if (uploadInterval < 5) {
      alert("上传周期必须 >= 5");
      return;
    }
    const params = new URLSearchParams({
      mode,  // wind / elevator
      interval: uploadInterval.toString(),
    });

    await fetch("/change-interval", {
      method: "POST",
      body: params,
    });
  };

  // 5. 上传模型
  const uploadModel = async () => {
    if (!modelFile) {
      alert("请选择模型文件后再上传");
      return;
    }
    const formData = new FormData();
    formData.append("file", modelFile);

    await fetch("/api/upload-model", {
      method: "POST",
      body: formData,
    });
  };

  // ------------------- 界面渲染 -------------------
  return (
    <div style={{ padding: "1rem" }}>
      <h1 style={{ fontWeight: "bold", marginBottom: "1rem" }}>系统管理</h1>

      {/* 选择模式：风电 / 电梯 */}
      <div style={{ marginBottom: "1rem" }}>
        <label style={{ marginRight: "8px" }}>选择模式：</label>
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="wind">win（风电）</option>
          <option value="elevator">ele（电梯，戴德）</option>
        </select>
      </div>

      {/* 修改 IP */}
      <div style={{ marginBottom: "1rem" }}>
        <input type="text" placeholder="新 IP 地址" value={ip} onChange={(e) => setIp(e.target.value)} style={{ marginRight: "8px" }} />
        <input type="text" placeholder="子网掩码" value={subnetMask} onChange={(e) => setSubnetMask(e.target.value)} style={{ marginRight: "8px" }} />
        <input type="text" placeholder="网关" value={gateway} onChange={(e) => setGateway(e.target.value)} style={{ marginRight: "8px" }} />
        <input type="text" placeholder="DNS 1" value={dns1} onChange={(e) => setDns1(e.target.value)} style={{ marginRight: "8px" }} />
        <input type="text" placeholder="DNS 2" value={dns2} onChange={(e) => setDns2(e.target.value)} style={{ marginRight: "8px" }} />
        <button onClick={changeIP}>修改 IP</button>
      </div>

      {/* 修改 MQTT */}
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="MQTT 地址"
          value={mqttAddress}
          onChange={(e) => setMqttAddress(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <input
          type="text"
          placeholder="MQTT 账号"
          value={mqttUsername}
          onChange={(e) => setMqttUsername(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <input
          type="text"
          placeholder="MQTT 密码"
          value={mqttPassword}
          onChange={(e) => setMqttPassword(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <button onClick={changeMQTT}>修改 MQTT</button>
      </div>

      {/* 修改后端地址 */}
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="后端地址"
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <input
          type="text"
          placeholder="后端端口"
          value={backendPort}
          onChange={(e) => setBackendPort(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <button onClick={changeBackend}>修改后端地址</button>
      </div>

      {/* 修改上传周期 */}
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="number"
          min={5}
          placeholder="上传周期(>= 5)"
          value={uploadInterval}
          onChange={(e) => setUploadInterval(parseInt(e.target.value, 10))}
          style={{ marginRight: "8px" }}
        />
        <button onClick={changeInterval}>修改上传周期（秒）</button>
      </div>

      {/* 上传模型
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="file"
          onChange={(e) => setModelFile(e.target.files[0])}
          style={{ marginRight: "8px" }}
        />
        <button onClick={uploadModel}>上传模型</button>
      </div> */}
    </div>
  );
}
