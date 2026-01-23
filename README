# Claw Cloud Auto Login

使用 DrissionPage 自动登录 claw.cloud，避免被识别为闲置账号导致 pod 被删除。

## 功能特性

- 自动登录 claw.cloud 和 ap-southeast-1.run.claw.cloud
- 防止账户因闲置而被删除
- 已登录状态检测（检测客户中心和GitHub头像）
- 邮件通知功能（登录成功/失败）
- 无头模式运行，后台自动操作

## 技术栈

- Python
- [DrissionPage](https://github.com/g1879/DrissionPage) - 网页自动化工具
- Selenium - 浏览器控制
- SMTP - 邮件通知

## 安装依赖

```bash
pip install DrissionPage
```

## 配置说明

### 1. 邮件配置

编辑 `xt_mail.py` 文件配置SMTP信息：

```python
smtp_config = {
    'smtp_server': 'smtpdm.aliyun.com',          # SMTP服务器地址
    'smtp_user': 'your_email@service.com',       # 发送方邮箱
    'smtp_password': os.environ.get('domain_smtp_pwd'), # 邮箱密码（通过环境变量设置）
    'sender': 'your_email@service.com',          # 发送方邮箱
    'receivers': [                               # 接收方邮箱列表
        "recipient1@example.com",
        "recipient2@example.com"
    ]
}
```

### 2. 环境变量

设置SMTP密码环境变量：
```bash
export domain_smtp_pwd=your_smtp_password
```

### 3. 浏览器配置

- 默认使用 Microsoft Edge 浏览器
- 浏览器配置文件保存在 `C:\temp\claw_cloud_profile`
- 使用固定端口 9222 进行连接

## 使用方法

直接运行主程序：

```bash
python claw_auto_login.py
```

程序将：
1. 自动启动Edge浏览器
2. 访问 https://claw.cloud/login 并使用GitHub账号登录
3. 访问 https://ap-southeast-1.run.claw.cloud 并登录
4. 检测登录状态并输出结果
5. 发送结果邮件通知

## 工作原理

- 使用 DrissionPage 控制浏览器进行自动化操作
- 智能检测已登录状态，避免重复登录
- 多种策略定位登录按钮（XPath、文本匹配等）
- 自动处理GitHub授权页面
- 支持在无头模式下运行

## 项目结构

```
claw-cloud-auto-login/
├── claw_auto_login.py      # 主程序 - 自动登录脚本
├── xt_mail.py             # 邮件模块 - 邮件发送功能
└── README                 # 项目说明文档
```

## 注意事项

- 需要预装 Microsoft Edge 浏览器
- 确保网络可以访问 claw.cloud 和 GitHub
- 首次运行时可能需要手动完成一次GitHub授权
- 程序会创建临时目录保存浏览器配置文件
- 邮件功能需要正确配置SMTP服务器

## 维护者

该项目由 xiatian 开发维护。

## 更新日志

- 修复: SMTP密码从环境变量获取
- 新增: 邮件通知结果功能
- 新增: 已登录检测逻辑
- 新增: app部署页面登录逻辑 (https://ap-southeast-1.run.claw.cloud)