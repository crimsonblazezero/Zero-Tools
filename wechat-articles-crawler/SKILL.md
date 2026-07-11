---
name: 公众号作者文章抓取
description: 用本地微信公众号抓取器批量识别并拉取某个公众号作者的历史文章，输出 Markdown、HTML 和 articles.json，供后续做作者语料库、风格拆解、仿写模板、事实核验和内容归档。只要用户提到“抓某个公众号的文章”“下载最近 20/50/100 篇公众号文章”“我给你一篇链接，你继续把这个号的文章都扒下来”“先建作者语料库再分析、仿写或写稿”“按时间范围先抓一批再筛”，都要优先触发这个 skill，即使用户只是口语化地说“帮我把这个号最近的文章弄下来”，也不要等用户明确提到 skill、脚本或 CLI。
---

## 这个 skill 负责什么

把“给我一个公众号文章链接，然后批量抓取这个公众号最近 N 篇文章并落盘”这件事标准化。

这个 skill 自带抓取脚本包，默认使用当前 skill 目录里的这些文件：

- `./scripts/main.py`
- `./scripts/requirements.txt`
- `./scripts/config.json`
- `./scripts/run_fetcher.sh`
- `./scripts/run.command`
- `./references/抓取器说明.md`

`./scripts/main.py` 是抓取主程序。`./scripts/run_fetcher.sh` 是 agent 更适合调用的启动脚本，会在 `scripts/` 目录下缺少 `.venv` 时自动创建并安装依赖。需要看工具细节、安装方式、JSON 返回和缓存目录时，再读 `./references/抓取器说明.md`。

下面这些情况不要硬用本 skill：

- 用户只要单篇文章摘要，不需要批量抓取
- 用户要做最终排版、发布、审查
- 用户要抓评论数、阅读数、点赞数等额外指标
- 用户要求云端缓存公众号登录态

## 你依赖的本地工具能力

当前抓取工具已经具备这些能力：

- 本地保存登录态，不走云端
- 登录失效时自动生成二维码
- 支持 `CLI + JSON`
- 支持 `ensure-login`
- 支持 `login-status`
- 支持 `fetch`
- 支持 `fetch --resume <上一轮articles.json>`（续抓，跨轮去重，不重复）
- 支持 `fetch --since/--until <YYYY-MM-DD>`（时间窗，跳过过期/过时旧文，**按中国时区 Asia/Shanghai 零点对齐**）
- 支持 `fetch --dry-run`（只返回将要抓取的清单，不落盘——配合时间窗做"先预览后决定"）
- 支持 `fetch --force-qr` / `--login-timeout` / `--qr-refresh`（登录增强）
- 支持 `fetch --safe` / `--fast`（限流预设：保守 / 激进）
- 支持 `fetch --md-only`（只输出 Markdown，不生成 HTML；也可在 `config.json` 设 `write_html:false` 作为永久默认）
- 去重增强：每轮在输出目录生成 `seen_urls.json` 清单，跨轮 / 跨次运行自动跳过已抓文章；**失败的会重试**，已下载的 Markdown 幂等复用
- 限流保护：后台 API 调用与文章下载均插入「固定间隔 + 随机抖动」，遇 `429` / `5xx` / "操作频繁" 自动指数退避
- 支持 `clear-login`
- 支持 `increment`（增量续抓：自动定位上次 output 目录、复用登录态、跳过已抓文章，公众号未来更新时一行命令搞定，绝不重复）
- 输出 `Markdown`、`HTML`、`articles.json`（用 `--md-only` 或 `config.json` 的 `write_html:false` 可只出 Markdown）

这个 skill 默认调用当前目录内自带的抓取器副本，不要回头依赖桌面上的原项目路径，除非用户明确要求你同步或升级那份原始项目。

## 运行前检查

先检查以下文件是否存在：

- `./scripts/main.py`
- `./scripts/requirements.txt`
- `./scripts/run_fetcher.sh`

如果缺失：

1. 明确告诉用户 skill 自带抓取器不完整。
2. 不要伪造抓取结果。
3. 如果用户要你补安装，再在当前 skill 目录里补齐。

## 输入约定

最小输入通常只需要：

- 任意一篇目标公众号文章链接

可选输入：

- 单次抓取篇数
- 输出父目录
- 是否需要清空已有登录态后重登
- 当前环境是 `IM`、纯终端、还是有桌面界面

如果用户没有显式给抓取篇数和输出目录：

- 优先沿用 `./scripts/config.json`
- 不要擅自改 `./scripts/main.py`
- 需要调数量或输出路径时，只改 `./scripts/config.json`

## 配置规则

工具当前通过 `./scripts/config.json` 控制这些参数：

- `output_parent`
- `output_folder_name`
- `article_limit`
- `concurrency`
- `display_mode`
- `write_html`（是否同时生成 HTML 文件，`true` 默认；设为 `false` 则只出 Markdown）

处理原则：

- 用户明确要求改输出目录或抓取篇数时，只改 `./scripts/config.json`
- 用户没要求时，沿用现有配置
- Linux / agent / IM 场景优先用 `display_mode = "silent"`
- 纯终端扫码场景优先用 `display_mode = "terminal"`
- 本机桌面人工扫码场景可用 `display_mode = "image"`

推荐直接调用：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh <subcommand> ...
```

## 标准工作流

### 1. 确认是否要清除登录态

默认不要清。

只有用户明确说：

- “删掉登录状态重新来”
- “我要测试从零登录”
- “我要把机器交给别人，先清缓存”

才执行：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh clear-login --json
```

### 2. 选择二维码展示模式

按场景选：

- IM / bot / agent 回消息：`silent`
- Linux 纯终端：`terminal`
- 本机有图形界面，用户直接扫码：`image`
- 不确定但有人机混合：`auto`

### 3. 确保登录可用

优先运行：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh ensure-login --json --display silent
```

如果返回 `authenticated`，直接继续。

> 登录增强：加 `--force-qr` 可忽略本地已缓存的登录态、强制重新扫码（用于缓存过期却没自动识别的场景）；`--login-timeout`（默认 1800s）控制二维码等待上限，`--qr-refresh`（默认 90s）控制二维码刷新间隔。微信二维码单码有效期约 90–120s，**务必只扫当前弹出的最新活码**，扫到旧码会一直 `waiting_scan`。

如果返回 `waiting_scan`：

- 读取 `qr_png_path` 和 `qr_text_path`
- IM / 聊天场景：优先把 `qr_png_path` 对应的图片发给用户
- 纯终端场景：打印或转述 `qr_text_path`
- 本机桌面场景：如果当前命令不是 `--display image`，可以改为 `--display image` 重新启动登录
- 然后轮询：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh login-status --json
```

直到出现：

- `status = authenticated`
- 或 `status = timeout`
- 或用户中止

### 4. 执行抓取

登录成功后，执行：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh fetch "公众号文章链接" --json --display silent
```

抓取成功时会返回：

- `account_name`
- `account_alias`
- `downloaded`
- `failed`
- `output_dir`
- `index_file`
- `results`

### 4.5 续抓模式（--resume）：抓超过 200 篇且不重复

单号硬上限为 `article_limit`（默认 200）篇。要抓“接下来”的文章且零重复，用 `--resume` 指向上一轮的 `articles.json`：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh fetch "公众号文章链接" --json --display silent \
  --resume "<上一轮输出目录>/articles.json"
```

续抓行为：

- 读取上一轮 `articles.json` 里的文章链接作为“已抓清单”，本轮自动跳过，实现跨轮去重
- 复用同一输出目录（不新建时间戳文件夹），新文章续写进 `markdown/`、文件名序号从已有 `.md` 数 +1 起，不会覆盖
- 续抓只写 Markdown，不生成 `html/`
- 新结果合并进同一 `articles.json`，累计篇数一目了然
- 轮到没有新文章时返回 0 篇，即该号历史已抓完

原理是**链接去重**而非硬算偏移（偏移在批次/多图文下会错位），所以放心一路 `--resume` 接力即可。

### 4.6 时间窗（--since / --until）：跳过过期/过时旧文

微信接口最新文章在最前。加时间窗后，遇到比 `--since` 更老的文章会**立即停**（后面全是更老的）；`--until` 丢弃比某天更新的文章（含当天，极少用）。

```bash
# 只抓 2024-07-08 之后（近2年），且跳过已抓
python main.py fetch "公众号文章链接" --json --since 2024-07-08 --resume "<上一轮输出目录>/articles.json"
# 只抓 2025 全年
python main.py fetch "公众号文章链接" --json --since 2025-01-01 --until 2025-12-31
# 先预览（不下载）近 2 年清单，确认无误再去掉 --dry-run 真抓
python main.py fetch "公众号文章链接" --json --since 2024-07-08 --dry-run
```

- `--since YYYY-MM-DD`：只保留发布时间 ≥ 该日期（比这老的跳过/停）——主要用去丢弃过期、内容过时、链接失效的旧文
- `--until YYYY-MM-DD`：只保留发布时间 ≤ 该日期（含当天）
- **时区对齐（已修正）**：默认按 **中国时区 `Asia/Shanghai`（UTC+8）零点**对齐。微信 `create_time` 是 UTC 秒，本工具会换算成"中国当天 0 点"再比较，避免旧版按 UTC 零点导致**差一天**的问题（例如 2024-07-08 07:09 的中国文章，旧版会被误判为"旧文"，新版正确归为"新文"）。
- 若需按世界时对齐，加 `--tz UTC`。
- 可与 `--resume`、`--dry-run` 组合使用。

### 4.7 预览模式（--dry-run）：先清单、后抓取

带 `--dry-run` 时，工具仍会登录并查询文章列表、应用时间窗与去重，但**不下载任何文件**，只返回 `would_download` 清单（含标题、链接、发布时间、已抓取标记）。非常适合"先看看会抓哪些，再决定要不要真落盘 / 删旧文"的工作流。

### 4.8 限流保护（避免触发公众号封禁）

为防止短时间内大量请求被腾讯识别为爬虫、触发**限流 / 封号**，工具在每一层都加了保护：

- **后台 API（`searchbiz` / `appmsgpublish`）**：每次调用前插入 `api_min_delay + 随机抖动` 的间隔（默认 ≈2.0+1.5s）。
- **文章下载**：每篇之间插入 `dl_min_delay + 随机抖动`（默认 ≈1.5+1.2s），并发默认降到 **3 路**（旧版是 6）。
- **自动退避**：遇到 `429` / `5xx` / 接口返回"操作频繁 / 频率"等，按 `backoff_base × 2^n` 指数退避后重试（默认最多 6 次）。
- **预设切换**：
  - `--safe`：保守模式，间隔加大、并发降到 2，速度最慢但最稳。
  - `--fast`：激进模式，间隔减小、并发拉到 5，速度最快但更易触发限流（风险自担）。
  - 也可用 `--min-delay` / `--max-jitter` 精细覆盖下载间隔。
- 这些参数都写在 `config.json` 的 `throttle` 字段里，可长期调。

### 4.9 不重复抓取（去重增强）

- **跨轮续抓**：`--resume` 读取上一轮 `articles.json`，只跳过其中 **status=ok** 的文章；**失败的不会进清单，下一轮会被重试**。
- **跨次清单**：每轮在输出目录写 `seen_urls.json`，记录所有已成功下载的归一化链接。即便不传 `--resume`，再次对同目录抓取也会自动跳过已抓文章。
- **幂等复用**：下载前若发现对应 Markdown 已存在且非空，直接复用，不再发请求。
- **归一化**：按 `__biz`/`mid`/`idx`/`sn` 归一化链接，忽略 `chksm`/`scene` 等无关参数与参数顺序，避免“同一篇被判成两篇”。

### 4.10 增量续抓（increment）：公众号未来更新，零重复一行搞定

首次完整抓取后，公众号今后每次发文，都不用重新跑全量、也不用记路径和日期。直接：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh increment --url "任意一篇该号文章链接" --json --display silent
```

它会自动做三件事：

1. 在 `output_root`（config 的 `output_parent/output_folder_name`）下找**最新的**含 `articles.json` 的抓取目录（即上次的结果）；
2. 用上一轮的 `articles.json` 作为“已抓清单”（`--resume` 等价物），翻页时跳过全部已抓文章，**新发的必然不在清单里，会被抓到**；
3. 复用同一输出目录，新文章续写进 `markdown/`、合并进同一个 `articles.json`。

行为要点：

- **默认不早停**：仅靠链接去重，翻到列表尽头才停——这是最稳的策略，**绝不漏抓**新文章，也不依赖旧 `articles.json` 是否带发布时间字段。
- 若想提速，可显式加 `--since YYYY-MM-DD` 做早停；但 `--since` 不能晚于“已抓最新文章的发布日”，否则翻页会提前停、漏掉中间的新文章。不确定就别加。
- 可加 `--dry-run` 先预览“将新增哪几篇”（不落盘），确认后再真抓。
- 可加 `--last-dir "<指定output目录>"` 强制指定上次目录（多号混抓、想精确控制时用）。
- `increment` 同样遵循 `config.json` 的 `write_html`（及临时 `--md-only`）：若已设为只出 Markdown，增量续抓也只写 Markdown，不会补生成 HTML。
- 若上次之后公众号**没更新**，不会报错，而是返回 `status = up_to_date`（“没有比上次更新的文章，无需抓取”）。
- 仍支持 `--safe` / `--fast` / `--force-qr` / `--login-timeout` / `--qr-refresh` 等全部选项。

> 与手动 `fetch --resume "<上次>/articles.json"` 完全等价，但省去了“记住上次路径 + 记住上次日期”的认知负担。种子链接仍用 `--url` 或位置参数传入，仅用于定位公众号。

### 5. 给出结果摘要

至少汇报这些信息：

- 命中的公众号名称
- 本次抓取篇数
- 成功 / 失败数量
- 输出目录
- `articles.json` 路径
- 当前登录态是“复用已有缓存”还是“本轮扫码新登录”

## 关于"指定时间范围"

工具现在**原生支持时间窗**：`--since` / `--until` 在后台翻页时就会按（默认中国时区的）发布日期过滤，遇到比 `--since` 更老的文章会立即停，不会把过期/过时旧文拉下来。

推荐工作流：

1. 先用 `--dry-run --since <起始日>` 预览将要抓取的清单（不落盘），确认范围与数量。
2. 确认无误后去掉 `--dry-run` 正式抓取；如需续抓加 `--resume`。
3. 若目标时间段跨度很大（超过单轮 `article_limit`），先调大 `article_limit` 或分多轮 `--resume` 接力。

这套时间窗已按中国时区对齐，不要再让用户"把截止日往前设 1 天"来补偿 UTC 偏移。

## 输出物说明

默认输出结构类似：

```text
<output_parent>/输出文章/<公众号名_时间戳>/
  markdown/
  html/            # 仅当开启 HTML 输出时存在（默认开启；--md-only 或 write_html:false 时不生成）
  articles.json
```

每篇文章通常会有：

- 一份 Markdown
- 一份原始 HTML（开启 HTML 输出时）

索引文件 `articles.json` 适合：

- 批量分析
- 后续仿写模板生成
- 做时间筛选
- 统计抓取成功率

## 隐私与安全边界

必须遵守：

- 登录态只允许保存在本机项目目录
- 不要把 `.playwright-profile` 上传到云端
- 不要把登录缓存打包发给别人
- 不要把 cookie、token、profile 内容直接展示给用户
- 除非用户明确要求，否则不要执行 `clear-login`

如果用户说要把机器或项目交给别人：

```bash
cd "内容生产龙虾/公众号作者文章抓取"
./scripts/run_fetcher.sh clear-login --json
```

并明确告诉用户已清理这两个目录：

- `.playwright-profile`
- `login_artifacts`

## 失败处理

### 登录相关

- 如果 `ensure-login` 长时间卡住，检查 `login-status --json`
- 如果二维码为空白，说明二维码文件生成异常，不能假装可扫
- 如果 `status = timeout`，提示用户重新发起登录

### 工具相关

- 如果 `./scripts/.venv/bin/python` 不存在，优先通过 `./scripts/run_fetcher.sh` 自动补环境
- 如果 `./scripts/main.py` 不存在，说明当前 skill 自带抓取器不完整
- 如果 `fetch` 失败，要把错误原样转述给用户，并附上当前命令和关键路径

### 抓取结果相关

- 如果 `downloaded = 0`，不能说“已完成”
- 如果 `failed > 0`，要明确说失败篇数和可能原因

## 推荐汇报格式

当状态是 `waiting_scan` 时，用这种结构：

```text
当前状态：等待扫码登录
二维码图片：<qr_png_path>
二维码文本：<qr_text_path>
下一步：请扫码，扫码后我继续轮询登录状态
```

当抓取完成时，用这种结构：

```text
抓取完成
公众号：<account_name>
抓取结果：成功 <downloaded> 篇，失败 <failed> 篇
输出目录：<output_dir>
索引文件：<index_file>
```

## 与其他内容生产 skill 的衔接

抓取完成后，常见下一跳是：

- `公众号作者仿写模板生成`
  - 用抓下来的 Markdown 建作者风格模板
- `公众号标题与开头拆解`
  - 重点拆标题、开头钩子和叙事切口
- `公众号文章写作`
  - 把作者风格和情报素材拼起来正式写稿
- `公众号信息深挖与多源核验`
  - 对抓到的主题继续做多源验证和补充事实

## 示例触发

**示例 1**

输入：把 Rockhazix 这个公众号最近 50 篇文章全抓下来，我后面要做仿写。

处理：触发本 skill，先确保登录，再批量抓取并返回输出目录。

**示例 2**

输入：我给你一篇公众号链接，你去把这个作者最近的文章都下载成 Markdown。

处理：触发本 skill，用 `fetch` 命令执行一条龙抓取。

**示例 3**

输入：先删掉登录状态，我重新扫码，你抓完后告诉我文章都存到哪了。

处理：先 `clear-login`，再 `ensure-login`，登录成功后执行 `fetch`。
