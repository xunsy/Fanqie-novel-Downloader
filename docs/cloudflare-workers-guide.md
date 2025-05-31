# Cloudflare Workers 反代部署指南

本指南将帮助您部署 Cloudflare Workers 反向代理，以避免番茄小说API访问被封锁的问题。

## 📋 前置要求

1. **Cloudflare 账户**：免费账户即可
2. **域名**（可选）：可以使用 Cloudflare 提供的免费 workers.dev 子域名

## 🚀 部署步骤

### 1. 登录 Cloudflare Dashboard

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 使用您的账户登录

### 2. 创建 Worker

1. 在左侧菜单中点击 **"Workers & Pages"**
2. 点击 **"Create application"**
3. 选择 **"Create Worker"**
4. 为您的 Worker 起一个名字，例如：`tomato-novel-proxy`
5. 点击 **"Deploy"**

### 3. 编辑 Worker 代码

1. 在 Worker 详情页面，点击 **"Edit code"**
2. 删除默认代码
3. 复制 `scripts/cloudflare-worker-proxy.js` 中的完整代码
4. 粘贴到编辑器中
5. 点击 **"Save and deploy"**

### 4. 获取 Worker 域名

部署成功后，您将获得一个类似以下格式的域名：
```
https://tomato-novel-proxy.your-username.workers.dev
```

### 5. 测试 Worker

在浏览器中访问：
```
https://your-worker-domain.workers.dev/test
```

如果看到类似以下的JSON响应，说明部署成功：
```json
{
  "status": "ok",
  "message": "Cloudflare Workers proxy is running",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## ⚙️ 配置下载器

### GUI版本配置

1. 打开番茄小说下载器
2. 点击 **"设置"** 按钮
3. 找到 **"Cloudflare Workers反代设置"** 区域
4. 勾选 **"启用 Cloudflare Workers 反代"**
5. 在 **"反代域名"** 输入框中填入您的 Worker 域名
   ```
   your-worker-domain.workers.dev
   ```
6. 建议保持 **"反代失败时回退到原始URL"** 选项勾选
7. 点击 **"测试连接"** 验证配置
8. 点击 **"保存设置"**

### CLI版本配置

编辑 `user_config.json` 文件，添加以下配置：

```json
{
  "cloudflare_proxy": {
    "enabled": true,
    "proxy_domain": "your-worker-domain.workers.dev",
    "fallback_to_original": true,
    "test_endpoint": "/test"
  }
}
```

## 🔧 高级配置

### 自定义域名（可选）

如果您有自己的域名，可以为 Worker 配置自定义域名：

1. 在 Worker 详情页面，点击 **"Settings"** 标签
2. 点击 **"Triggers"** 部分的 **"Add Custom Domain"**
3. 输入您的自定义域名，例如：`api.yourdomain.com`
4. 按照提示完成DNS配置

### 修改允许的域名列表

如果需要代理其他域名，可以修改 Worker 代码中的 `ALLOWED_HOSTS` 数组：

```javascript
const ALLOWED_HOSTS = [
  'fqphp.gxom.cn',
  'api.cenguigui.cn', 
  'lsjk.zyii.xyz',
  'nu1.jingluo.love',
  'nu2.jingluo.love',
  'fanqienovel.com',
  'your-additional-domain.com'  // 添加新域名
];
```

## 📊 使用统计

Cloudflare 免费计划提供：
- **每天 100,000 次请求**
- **每次请求最多 10ms CPU 时间**
- **全球边缘网络加速**

对于个人使用完全足够。

## 🛠️ 故障排除

### 1. Worker 无法访问

**问题**：访问 Worker 域名返回错误

**解决方案**：
- 检查 Worker 是否已正确部署
- 确认域名拼写正确
- 等待几分钟让部署生效

### 2. 代理请求失败

**问题**：下载器显示反代连接失败

**解决方案**：
- 检查 Worker 代码是否正确复制
- 确认目标域名在 `ALLOWED_HOSTS` 列表中
- 查看 Worker 日志（在 Dashboard 中）

### 3. 请求被限制

**问题**：大量请求后出现限制

**解决方案**：
- 检查是否超出免费计划限制
- 考虑升级到付费计划
- 调整下载器的请求频率

## 🔒 安全注意事项

1. **不要公开分享您的 Worker 域名**，避免被滥用
2. **定期检查 Worker 日志**，确保没有异常请求
3. **考虑添加访问控制**，如 IP 白名单或 API 密钥验证

## 📝 更新 Worker

当需要更新 Worker 代码时：

1. 在 Cloudflare Dashboard 中找到您的 Worker
2. 点击 **"Edit code"**
3. 更新代码
4. 点击 **"Save and deploy"**

## 💡 提示

- Worker 部署后通常在几分钟内全球生效
- 建议在不同地区测试连接性
- 可以创建多个 Worker 作为备份
- 定期备份 Worker 代码

## 📞 支持

如果遇到问题：

1. 检查 Cloudflare Workers 文档
2. 查看项目的 GitHub Issues
3. 确认网络连接正常
4. 验证配置文件格式正确

---

**注意**：Cloudflare Workers 反代功能仅用于学习和研究目的，请遵守相关法律法规和服务条款。
