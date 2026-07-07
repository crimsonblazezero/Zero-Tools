# 公众号文章续抓（--resume）用法

> 改造文件：`wechat_crawler/scripts/main.py`
> 原理：**链接去重**，不是硬算偏移。微信接口最新文章在最前，把上一轮 `articles.json` 里的链接当"已抓清单"，本轮从 `begin=0` 起但跳过清单里的链接，自然接到上一轮之后的下一批，跨轮零重复。

## 第 1 轮（首次抓取，你已做过）
```bash
cd wechat_crawler/scripts
./.venv/Scripts/python main.py fetch "https://mp.weixin.qq.com/s/DSmn68-zXHb0zLTU8fmmsA" --json
# 产出：wechat_export/输出文章/从宇宙大爆炸到PPC_20260708_062212/{markdown/, articles.json}
```

## 第 2 轮（抓接下来的 200 篇，不重复）
```bash
cd wechat_crawler/scripts
./.venv/Scripts/python main.py fetch "https://mp.weixin.qq.com/s/DSmn68-zXHb0zLTU8fmmsA" --json \
  --resume "../wechat_export/输出文章/从宇宙大爆炸到PPC_20260708_062212/articles.json"
# → 自动跳过第1轮那 200 篇，抓接下来 200 篇，写入同一目录
```

## 第 N 轮
把 `--resume` 指向**上一轮**的 `articles.json` 即可，循环往复直到没有新文章（返回 0 篇 = 历史抓完）。

## 续抓行为说明
- **不重复**：跨轮按文章链接去重（已修原脚本"整页旧文即误停"的 bug，能跨过全是旧文的页面继续往后翻）。
- **同目录续写**：续抓复用上一轮目录，不会每次新建时间戳文件夹；新文章 `markdown/` 文件名序号从已有 `.md` 数 +1 起，不覆盖。
- **只写 Markdown**：续抓模式不生成 `html/`（符合你只要 Markdown 的偏好）。
- **索引合并**：新结果追加进同一个 `articles.json`，累计篇数一目了然。

## 时间窗（--since / --until）—— 跳过过期/过时旧文

微信接口**最新文章在最前**。加时间窗后，抓取遇到比 `--since` 更老的文章会**立即停**（后面全是更老的，没必要再抓）；`--until` 用于丢弃比某天更新的文章（极少用）。

- `--since YYYY-MM-DD`：只保留发布时间 ≥ 该日期的文章（比这老的跳过/停）。**主要用去丢弃过期、内容过时、链接可能失效的旧文。**
- `--until YYYY-MM-DD`：只保留发布时间 ≤ 该日期的文章（含当天；比这新的跳过）。
- 两个可组合：`--since 2024-01-01 --until 2024-12-31` 只抓 2024 全年。
- 截止日按 **UTC 零点**对齐（与微信 `create_time` 一致）。中国用户按北京时间核对若差一天，把截止日往前设 1 天即可。

```bash
# 只抓 2024-07-08 之后（近2年）的文章，且跳过已抓的
./.venv/Scripts/python main.py fetch "https://mp.weixin.qq.com/s/DSmn68-zXHb0zLTU8fmmsA" --json \
  --since 2024-07-08 \
  --resume "../wechat_export/输出文章/从宇宙大爆炸到PPC_20260708_062212/articles.json"

# 只抓 2025 全年，全新号
./.venv/Scripts/python main.py fetch "https://mp.weixin.qq.com/s/DSmn68-zXHb0zLTU8fmmsA" --json \
  --since 2025-01-01 --until 2025-12-31
```

> 已实测：时间窗逻辑（since 越过即停 / until 含当天 / 组合 / 解析非法日期报错）均通过离线单测。

## 注意
- 仍需微信扫码登录（登录态在 `PROFILE_DIR`，未过期可免扫直接抓；过期则重新弹码）。
- 单号每轮上限 200 篇（工具硬上限），超出的靠多轮 `--resume` 接力。
- 微信对历史接口有**频率控制**（触发 `freq control ret:200013` 会暂停），非内容上限；冷却后可 `--resume` 重试补抓。
- `--since/--until/--resume` 改动已同步回 `D:\AgentSystem\shared_skills\wechat-articles-crawler\scripts/main.py`（受同步机制管理，会传播到其他实例）。
