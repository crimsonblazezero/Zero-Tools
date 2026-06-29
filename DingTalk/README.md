# DingTalk CLI & Skills Suite (钉钉工具与技能套件)

本目录归档了项目所需的所有钉钉命令行工具（CLI）、会话认证凭证以及专有的技能库（Skills），以实现跨设备一键迁移与“开箱即用”。

---

## 📂 目录结构 (Directory Structure)

```
DingTalk/
├── dingtalk-auth.json   # 导出的登录认证凭证 (Session Credentials)
├── bin/                 # 钉钉 CLI 可执行文件 (Executable Engine)
│   ├── dws.cmd          # Windows 批处理调用入口
│   └── dws.exe          # 编译好的 Go 二进制 CLI (v1.0.41)
└── skills/              # 钉钉专属技能库 (DingTalk Custom Skills)
    ├── dws/             # 核心 DWS 技能与产品参考
    ├── dingtalk-unified/# 钉钉全能套件技能
    └── connector-dingtalk/# 连接器产品模块文档
```

---

## 🚀 快速启用指南 (Quick Start Guide)

在新电脑或 VPS 上拉取代码后，如需使用钉钉技能，请执行以下两步：

### 第一步：导入认证包 (Import Credentials)
进入 `DingTalk/bin/` 目录，或者直接在项目根目录下，运行以下 PowerShell 指令导入登录状态：
```powershell
# 导入凭据
& "DingTalk/bin/dws.cmd" auth import --file "DingTalk/dingtalk-auth.json"
```

### 第二步：验证登录状态 (Verify Connection)
运行以下命令确认认证是否成功生效：
```powershell
& "DingTalk/bin/dws.cmd" auth status
```
若返回 `success: true` 及您的账户信息，即代表配置成功。

---

## 🛠️ CLI 命令调用规范 (CLI Invocation)

在开发脚本或让 AI 助手调用时，请指定本地相对路径：
- Windows 环境：`& "DingTalk/bin/dws.cmd" <service> <command> [flags]`
- 添加 `-y` / `--yes` 跳过确认提示以实现自动化。
- 追加 `--format json` 确保输出结构化，便于程序解析。

示例（搜索联系人）：
```powershell
& "DingTalk/bin/dws.cmd" contact user search --query "王祎" --format json
```
