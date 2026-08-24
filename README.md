# 医道同修 · 每日推送（GitHub Actions 版）

每天早上 **8:30（北京时间）** 自动把「医道同修」中医学习内容发到邮箱，与本地电脑是否开机无关。

- 课程周期：2026-08-25 ~ 2026-11-22，共 90 期（总第001期 ~ 总第090期）
- 邮件内容：墨绿横幅 + 正文 + 讨论题 + **内嵌长图**（可直接保存转发微信群）
- 全部 90 期内容和长图已预生成，存放在 `data/` 目录，脚本只负责按时发送
- 仅用 Python 标准库，无第三方依赖

## 目录结构

```
yidao-daily-push/
├── .github/workflows/daily-email.yml   # 定时任务（每天 00:30 UTC = 北京 8:30）
├── send_daily.py                       # 发信脚本
├── data/
│   ├── issues.json                     # 90期内容数据
│   └── images/                         # 90张长图（第001期.png ~ 第090期.png）
└── README.md
```

## 首次部署（一次性，约 5 分钟）

### 1. 获取 163 邮箱 SMTP 授权码

163 邮箱不能用登录密码发信，需要专门生成"授权码"：

1. 网页登录 163 邮箱 → **设置** → **POP3/SMTP/IMAP**
2. 开启 **SMTP 服务**（可能需要手机验证）
3. 点"新增授权密码"，按提示生成，**复制保存**（只显示一次）

### 2. 推送本仓库到 GitHub

```bash
cd yidao-daily-push
git remote add origin git@github.com:<你的用户名>/yidao-daily-push.git
git push -u origin main
```

> 仓库可以设为 Private，定时任务在私有仓库同样有效（免费账户每月 2000 分钟额度，本任务每次约 1 分钟，足够用）。

### 3. 配置 Secrets

GitHub 仓库页面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**，添加三个：

| Name | Value |
|------|-------|
| `SMTP_USER` | 发件邮箱，如 `houkep@163.com` |
| `SMTP_PASSWORD` | 第 1 步生成的 SMTP 授权码 |
| `TO_EMAIL` | 收件邮箱，如 `houkep@163.com` |

### 4. 手动测试一次

仓库页面 → **Actions** 标签 → 左侧选 **daily-email** → 右侧 **Run workflow** → 点运行。

到邮箱确认收到「医道同修·总第001期」邮件（今天是 8/24，正式开课前脚本按当天日期计算，手动测试默认发第001期内容）、长图是否正常显示。**测试通过后，从明天 8/25 起每天自动发送。**

## 常用操作

```bash
# 本地手动发某一期（测试用）
SMTP_PASSWORD=你的授权码 FORCE_ISSUE=1 python3 send_daily.py

# 课程结束后脚本自动停发（日期超出 2026-11-22 即退出），无需处理
```

## 说明

- GitHub 定时任务偶尔延迟几分钟（一般 5-15 分钟内），介意可把 cron 提前，如 `15 0 * * *`（北京 8:15）
- 若连续 60 天仓库无活动 GitHub 会暂停定时任务，本课程 90 天内有持续运行记录，不受影响
- 换收件邮箱：只需修改 GitHub Secrets 里的 `TO_EMAIL`
