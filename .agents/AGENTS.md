# RTK Token Optimization (Windows Mode)

> Windows 环境下无 bash hook，通过此文件注入 RTK 使用规则。

## 核心规则：所有 Shell 命令必须加 `rtk` 前缀
在此项目中运行 any shell 命令时，**始终**在命令前加 `rtk` 前缀以节省 60-90% token：
- rtk git status
- rtk git diff
- rtk pip install
