# API 延迟模式与解决方案

## 模式 1：服务端间歇性延迟

**特征**：
- 首次连接正常，后续请求变慢
- 延迟 10-30s，无错误但超时
- Ping 测试显示丢包

**原因**：
- 云服务过载
- CDN/网关节点问题
- 区域性网络拥塞

**解决方案**：
1. 增加 `gateway_timeout`（默认 1800s，可尝试 300s 快速失败）
2. 检查服务商状态页
3. 考虑切换区域端点

## 模式 2：客户端配置错误

**特征**：
- 恒定性 400/401/403 错误
- 日志显示 schema 验证失败
- 升级后立即出现

**原因**：
- api_mode 未显式设置
- API key 失效
- 端点 URL 变更

**解决方案**：
1. 检查 `hermes config get model`
2. 验证 API key：`hermes auth status`
3. 确认 base_url 正确

## 模式 3：Session 数据污染

**特征**：
- 第一句正常，第二句失败
- 错误包含 "output_text" 或格式不匹配
- 特定 session 持续失败

**原因**：
- 旧版 Hermes 使用不同消息格式
- 混用不同 provider 的历史消息
- Codex Responses API 格式残留

**解决方案**：
1. 检查 session 数据：`hermes sessions list`
2. 创建新 session 测试：`/new`
3. 清理旧 session：`hermes sessions delete <id>`

## 模式 4：网络代理干扰

**特征**：
- 随机超时
- 某些请求成功，某些失败
- VPN/代理切换后出现

**原因**：
- 代理服务器不稳定
- DNS 解析问题
- 地区性网络限制

**解决方案**：
1. 临时禁用代理测试
2. 使用 `curl --noproxy "*"` 直连测试
3. 检查 hosts 文件