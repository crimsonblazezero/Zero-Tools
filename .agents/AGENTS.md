# RTK Token Optimization (Windows Mode)

> Windows 环境下无 bash hook，通过此文件注入 RTK 使用规则。
> RTK 安装路径: `C:\Users\Administrator\.local\bin\rtk.exe`

## 核心规则：所有 Shell 命令必须加 `rtk` 前缀

在此项目中运行任何 shell 命令时，**始终**在命令前加 `rtk` 前缀以节省 60-90% token：

```powershell
# Git 操作
rtk git status          # 代替: git status
rtk git diff            # 代替: git diff
rtk git log -n 10       # 代替: git log
rtk git add .           # 代替: git add
rtk git commit -m "msg" # 代替: git commit

# 文件操作
rtk ls .                # 代替: ls / dir
rtk grep "pattern" .    # 代替: grep

# 测试/构建
rtk cargo test          # 代替: cargo test
rtk npm test            # 代替: npm test
rtk pytest              # 代替: pytest

# 容器
rtk docker ps           # 代替: docker ps
```

## 统计命令

```powershell
rtk gain              # 查看 token 节省统计
rtk gain --history    # 最近命令历史
rtk discover          # 发现遗漏的 RTK 使用机会
```

## 为什么这样做

RTK 在命令输出到达 LLM context 之前进行过滤和压缩，节省 60-90% tokens。
**Windows 原生环境下无自动 hook，必须手动在命令前加 `rtk`。**
