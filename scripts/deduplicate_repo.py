# 仓库数据去重清理脚本
import shutil
from pathlib import Path

repo_root = Path("d:/Zero Tools")

targets_to_remove = [
    repo_root / "skills" / "superpower" / "skills",
    repo_root / "wechat-articles-crawler",
    repo_root / "lottie-player" / "skills" / "text-to-lottie",
    repo_root / "skills" / "ui-ux-pro-max" / ".shared",
]

for target in targets_to_remove:
    if target.exists():
        print(f"Removing duplicate target: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

print("Deduplication complete!")
