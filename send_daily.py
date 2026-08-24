#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医道同修 · 每日推送脚本
根据日期找到对应期号，从 data/issues.json 取内容，组装 HTML 富文本邮件，
长图以内嵌图片(CID)方式放进正文，通过 SMTP 发送。
仅用 Python 标准库，无第三方依赖。

环境变量：
  SMTP_USER      发件邮箱（默认 houkep@163.com）
  SMTP_PASSWORD  邮箱 SMTP 授权码（163邮箱需在设置中生成，不是登录密码）
  SMTP_HOST      默认 smtp.163.com
  SMTP_PORT      默认 465（SSL）
  TO_EMAIL       收件邮箱（默认与发件邮箱相同）
  FORCE_ISSUE    （可选）手动指定期号发送，用于测试，如 FORCE_ISSUE=1
"""
import json
import os
import smtplib
import sys
from datetime import date, datetime
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSE_START = date(2026, 8, 25)   # 第001期
COURSE_END = date(2026, 11, 22)    # 第090期
TOTAL = 90


def week_no(issue: int) -> int:
    """第1周为8/25-8/30特殊短周（第001-006期），第7期起每7天一周"""
    if issue <= 6:
        return 1
    return (issue - 7) // 7 + 2


def load_issue():
    with open(os.path.join(BASE_DIR, "data", "issues.json"), encoding="utf-8") as f:
        issues = json.load(f)
    issues = {i["issue"]: i for i in issues}

    forced = os.environ.get("FORCE_ISSUE")
    if forced:
        return issues[int(forced)], True

    today = date.today()
    if today < COURSE_START:
        print(f"课程尚未开始（{COURSE_START} 开课），今日不发送。")
        return None, False
    if today > COURSE_END:
        print("课程已结束，今日不发送。")
        return None, False
    issue_no = (today - COURSE_START).days + 1
    return issues[issue_no], False


def build_html(it: dict) -> str:
    """组装邮件正文 HTML（样式全部内联）"""
    n = it["issue"]
    meta_line = (
        f"医道同修 · 总第{n:03d}期 · 第{week_no(n)}周 · {it['column']} · "
        f"难度：{it['difficulty']}"
    )
    paragraphs = []
    for sec in it["sections"]:
        paragraphs.append(
            f'<p><b>{sec["h"]}</b></p>\n<p>{sec["p"]}</p>'
        )
    body_html = "\n".join(paragraphs)

    source = it["source_text"]
    if it.get("source_url"):
        source = f'<a href="{it["source_url"]}">{source}</a>'

    has_image = os.path.exists(os.path.join(BASE_DIR, "data", it["image"]))
    if has_image:
        img_block = (
            '<div style="background:#fff8e1;border-left:4px solid #f0a500;'
            'padding:10px 14px;border-radius:4px;font-size:14px;color:#7a5b00;'
            'margin:16px 0 8px;">💡 <b>核心：长图已包含全部排版内容</b>（顶栏+正文+讨论题+资料来源），'
            '<b>直接保存图片发到微信群</b>即可，无需复制文字。<br>'
            '📎 附件栏还有独立 <b>第{n:03d}期.png</b> 可下载；📋 邮件下方"切换纯文本"可复制不带格式的纯文字版。</div>\n'
            '<img src="cid:dailycard" style="max-width:640px;width:100%;'
            'display:block;margin:0 auto 8px;border-radius:6px;'
            'box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
        ).format(n=it["issue"])
    else:
        img_block = (
            '<p style="font-size:13px;color:#999;">⚠️ 今日长图缺失，仅发送文字版。</p>'
        )

    disclaimer = it.get("disclaimer") or "本内容仅供学习交流，不能替代医生诊疗。"

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f2f2f2;">
<div style="max-width:640px;margin:0 auto;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#333;line-height:1.8;padding:16px 12px;">

  <div style="background:#2d5a3d;color:#fff;padding:16px 24px;border-radius:8px 8px 0 0;">
    <div style="font-size:13px;opacity:0.85;letter-spacing:1px;">{meta_line}</div>
    <div style="font-size:22px;font-weight:bold;margin-top:6px;">{it["title"]}</div>
  </div>

  <div style="background:#faf9f5;padding:24px;border:1px solid #e8e4da;border-radius:0 0 8px 8px;">
    {body_html}

    <div style="background:#eef5ef;border-left:4px solid #2d5a3d;padding:10px 14px;border-radius:4px;margin:20px 0;">
      <b>💬 今日讨论</b><br>
      {it["discussion"]}
    </div>

    {img_block}

    <p style="font-size:13px;color:#888;">📚 资料来源：{source}</p>
    <p style="font-size:13px;color:#888;">{disclaimer}</p>
  </div>

  <p style="text-align:center;font-size:12px;color:#aaa;margin-top:12px;">—— 医道同修 · 总第{n:03d}期 · 内容可直接复制转发到微信群 ——</p>
</div>
</body></html>"""


def build_plain_text(it: dict) -> str:
    """生成不带任何 HTML 标记的纯文本版（便于复制粘贴到微信等不支持富文本的地方）"""
    n = it["issue"]
    lines = [
        f"医道同修·总第{n:03d}期·第{week_no(n)}周·{it['column']}·难度：{it['difficulty']}",
        it["title"],
        "",
    ]
    for sec in it["sections"]:
        lines.append(sec["h"])
        lines.append(sec["p"])
        lines.append("")

    lines.append("💬 今日讨论")
    lines.append(it["discussion"])
    lines.append("")

    has_image = os.path.exists(os.path.join(BASE_DIR, "data", it["image"]))
    if has_image:
        lines.append("——————")
        lines.append(f"💡 长图（含全部排版）已嵌入邮件正文，并作为附件发送。")
        lines.append(f"   直接保存图片发到微信群即可，无需复制此文字版。")
        lines.append("")

    lines.append(f"📚 资料来源：{it['source_text']}")
    if it.get("source_url"):
        lines.append(f"   {it['source_url']}")
    lines.append(it.get("disclaimer") or "本内容仅供学习交流，不能替代医生诊疗。")
    lines.append("")
    lines.append(f"—— 医道同修 · 总第{n:03d}期 · 内容可直接复制转发到微信群 ——")
    return "\n".join(lines)


def send(it: dict):
    user = os.environ.get("SMTP_USER", "houkep@163.com")
    password = os.environ["SMTP_PASSWORD"]
    host = os.environ.get("SMTP_HOST", "smtp.163.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    to_email = os.environ.get("TO_EMAIL", user)

    n = it["issue"]
    # 外层 mixed：同时承载正文和附件
    msg = MIMEMultipart("mixed")
    msg["Subject"] = Header(
        f"医道同修·总第{n:03d}期 {it['column']}：{it['title']}", "utf-8"
    )
    msg["From"] = formataddr(("医道同修", user))
    msg["To"] = to_email
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")

    # 内层 related：HTML 正文 + 内嵌图片（让 <img src="cid:dailycard"> 能找到图）
    related = MIMEMultipart("related")
    related.attach(MIMEText(build_html(it), "html", "utf-8"))

    img_path = os.path.join(BASE_DIR, "data", it["image"])
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_data = f.read()
        # 1) 正文内嵌图片（CID 方式，正文里直接显示）
        inline_img = MIMEImage(img_data)
        inline_img.add_header("Content-ID", "<dailycard>")
        inline_img.add_header("Content-Disposition", "inline",
                              filename=("utf-8", "", f"第{n:03d}期.png"))
        related.attach(inline_img)

    # 再外层 alternative：让客户端/网页可选 text/plain 或 text/html
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(build_plain_text(it), "plain", "utf-8"))
    alt.attach(related)
    msg.attach(alt)

    # 2) 可下载附件（用户可直接保存/转发）
    if os.path.exists(img_path):
        att_img = MIMEImage(img_data)
        att_img.add_header("Content-Disposition", "attachment",
                           filename=("utf-8", "", f"第{n:03d}期.png"))
        msg.attach(att_img)

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.sendmail(user, [to_email], msg.as_string())

    print(f"✅ 已发送：总第{n:03d}期（{it['date']}）{it['column']}：{it['title']} -> {to_email}")


def main():
    issue, _ = load_issue()
    if not issue:
        return
    if not os.environ.get("SMTP_PASSWORD"):
        print("❌ 缺少环境变量 SMTP_PASSWORD（邮箱 SMTP 授权码）")
        sys.exit(1)
    send(issue)


if __name__ == "__main__":
    main()
