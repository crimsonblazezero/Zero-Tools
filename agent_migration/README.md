# AI Agent 本地迁移与多 Agent 共享环境配置指南
## AI Agent Local Migration & Multi-Agent Sharing Guide

本目录包含用于将 AI Agent（Codex、Hermes、Antigravity、WorkBuddy）的数据与缓存目录由 C 盘迁移至 D 盘（或其他数据盘），并建立多 Agent 共享技能（SKILLs）与环境的自动化脚本与操作说明。

---

### 目录文件说明 / Files in this directory
1. **`migrate.ps1`**：通用 PowerShell 迁移与联接（Junction Link）建立脚本。
2. **`shared_skills.zip`**：当前已安装的共享技能（SKILLs）压缩包，用于公司电脑的首次初始化。
3. **`README.md`**：本指南文档。

---

### 公司电脑配置步骤 / Office Computer Setup Steps

#### 第一步：拉取仓库 / Pull Repository
在公司电脑的项目目录下执行 `git pull`，拉取最新的 `agent_migration` 目录文件。

#### 第二步：准备目标路径 / Prepare Target Directory
默认目标迁移根目录为 `D:\AgentSystem`。如需迁移至其他盘符（如 E 盘），请以文本编辑器打开 `migrate.ps1`，修改首行的驱动器变量：
```powershell
$targetDrive = "E:"  # 默认 D:，可按需修改
```

#### 第三步：关闭所有智能体软件 / Close All AI Software
务必彻底关闭公司电脑上运行的以下程序，防止文件被占用导致迁移失败：
* Codex 客户端 / Cherry Studio / Chatbox
* Hermes Agent 进程
* WorkBuddy 进程
* Antigravity IDE 窗口 / 终端命令行
* CC Switch 代理客户端

#### 第四步：以管理员身份运行脚本 / Run Script as Administrator
1. 以 **管理员身份** 启动 PowerShell。
2. 进入本目录并执行 `migrate.ps1` 脚本：
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   .\migrate.ps1
   ```
3. 脚本会自动迁移 C 盘对应的 Agent 数据目录，并建立目录联接（Junction Link）。

#### 第五步：解压共享技能包 / Extract Shared Skills
1. 将本目录下的 `shared_skills.zip` 解压。
2. 将解压出来的所有文件夹（如 `agnes-imagegen` 等）直接放入公司电脑新建的共享技能目录中：
   * 物理路径：`D:\AgentSystem\shared_skills\`
3. 此时，公司电脑上的所有 Agent 将会自动读取并共享这些技能。

---

### 双端技能自动同步配置（使用百度网盘同步空间）
### Autocompleted Syncing with Baidu Netdisk

为了让家里和公司的技能文件夹实时同步，建议使用百度网盘的**「同步空间」**功能：

1. **选择同步目录**：
   在百度网盘的「同步空间」中，新建同步对，将本地同步路径分别指定为两台电脑上的技能物理路径：
   `D:\AgentSystem\shared_skills`
2. **运作机制**：
   * 在家里电脑新增或更新一个技能（例如添加了新的 `SKILL.md`）。
   * 百度网盘在后台自动将 `shared_skills` 内的变动同步至云端。
   * 公司电脑开机后，网盘自动将改动下载到公司电脑的 `D:\AgentSystem\shared_skills`。
   * 因为有目录联接的存在，公司电脑上的所有 Agent 将瞬间识别并同步使用该技能，无需任何手动拷贝。

> [!WARNING]
> **绝对禁止同步整个 `D:\AgentSystem` 根目录**
> * 智能体运行时会锁定 `.sqlite` 数据库文件，同步软件会因「文件被占用」频繁报错，甚至导致数据库损坏。
> * `venv`（Python虚拟环境）和 `node_modules` 包含大量小文件且与本地硬件绑定，强行同步会导致网盘卡死或依赖崩溃。
> * **只需且仅需同步 `shared_skills` 文件夹！**
