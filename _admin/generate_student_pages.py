#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学员页生成器 (Tier 2 · 每学员独立不可猜页面)
============================================
适用：Chuck 的商科 / 咨询课，每位学员一份只属于自己的讲义页。
站点为纯静态（无后端），无法做"用户名+密码"真认证；本脚本用
「独立、随机、不可猜测的页面地址 + 微信私发」实现每学员隔离。

用法：
  1) 在本目录 students.csv 填写：code,name,doc
     - doc = 腾讯文档「分享 → 嵌入」拿到的 <iframe src="..."> 或 直接链接
     - 多个讲义用 | 分隔（例如 第1讲链接|第2讲链接）
  2) 运行：  python generate_student_pages.py
  3) 产出：
     - ../courses/s/<token>.html   每位学员一页（只含他自己的讲义）
     - student_links.csv           本地私发对照表（请勿部署 / 勿公开）
依赖：仅 Python 3 标准库，无需第三方包。
"""
import csv
import os
import re
import secrets
import html
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "courses", "s")
LINKS_CSV = os.path.join(HERE, "student_links.csv")
STUDENTS_CSV = os.path.join(HERE, "students.csv")

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name} · 专属讲义 | Chuck Tian</title>
<style>
  :root{{--navy:#0E2240;--accent:#2D6CDF;--bg:#F5F8FC;--ink:#1B2533;--muted:#5A6678;--line:#E3E9F2}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}}
  .nav{{background:var(--navy);padding:16px 22px;display:flex;align-items:center;justify-content:space-between}}
  .brand{{color:#fff;font-weight:700;letter-spacing:.3px}}
  .brand span{{color:#9fc2f5}}
  .nav a{{color:#cfe0f7;font-size:14px;font-weight:600}}
  .wrap{{max-width:1000px;margin:0 auto;padding:0 20px}}
  .hero{{background:var(--navy);color:#fff;padding:40px 0 34px}}
  .hero h1{{font-size:26px;margin:8px 0 6px}}
  .hero p{{color:rgba(255,255,255,.82);font-size:14px}}
  .badge{{display:inline-block;font-size:12px;font-weight:700;color:var(--accent);background:#E8F0FC;border-radius:6px;padding:3px 10px}}
  section{{padding:30px 0}}
  .doc{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(20,40,80,.04)}}
  .doc h3{{color:var(--navy);font-size:17px;margin-bottom:4px}}
  .doc .meta{{font-size:12px;color:var(--muted);margin-bottom:12px}}
  .frame{{position:relative;width:100%;padding-top:75%;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fafcff}}
  .frame iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:0}}
  .warn{{background:#fbf0e3;border:1px solid #f0d9bf;color:#8a5a1e;border-radius:10px;padding:12px 14px;font-size:13px;margin-top:6px}}
  footer{{text-align:center;color:var(--muted);font-size:12px;padding:26px 0}}
  a{{color:var(--accent);text-decoration:none}}
</style>
</head>
<body>
<div class="nav"><div class="brand">Chuck<span>.</span>OPC</div><a href="{home}">← 返回首页</a></div>
<section class="hero"><div class="wrap">
  <span class="badge">STUDENT ZONE · 专属讲义</span>
  <h1>{name}，这是你的专属讲义页</h1>
  <p>本页只显示你本人的课程讲义，请妥善保管链接，勿转发他人。</p>
</div></section>
<section><div class="wrap">
{docs}
  <div class="warn">提示：讲义由腾讯文档嵌入展示。如显示「无权限」，说明 Chuck 尚未为你开通该文档的查看权限，请微信联系 Chuck 开通。</div>
</div></section>
<footer>© {year} Chuck Tian · AI &amp; Strategy OPC · 专属内容，仅供本人查看</footer>
</body>
</html>"""

DOC_TEMPLATE = """  <div class="doc">
    <h3>{title}</h3>
    <div class="meta">腾讯文档 · 点击右上角可全屏 / 下载</div>
    <div class="frame"><iframe src="{src}" allowfullscreen></iframe></div>
  </div>"""


def extract_src(cell):
    cell = (cell or "").strip()
    if not cell:
        return None
    if "<iframe" in cell.lower():
        m = re.search(r'src=["\']([^"\']+)["\']', cell, re.I)
        return m.group(1) if m else None
    return cell  # 视为直接链接


def main():
    if not os.path.exists(STUDENTS_CSV):
        print("未找到 students.csv，请先按 students.csv 示例创建。")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    with open(STUDENTS_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    used = set()
    links = []
    for r in rows:
        code = (r.get("code") or "").strip()
        name = (r.get("name") or "").strip()
        docs_raw = (r.get("doc") or "").strip()
        if not name:
            print("· 跳过：缺少 name 的行（code=%s）" % code)
            continue
        srcs = [extract_src(x) for x in docs_raw.split("|")]
        srcs = [s for s in srcs if s]
        if not srcs:
            print("· 跳过：%s 无有效讲义链接" % name)
            continue
        while True:
            tok = secrets.token_hex(4)  # 8 位十六进制，不可猜
            if tok not in used:
                used.add(tok)
                break
        docs_html = ""
        for i, s in enumerate(srcs, 1):
            docs_html += DOC_TEMPLATE.format(title="讲义 %d" % i, src=html.escape(s, quote=True))
        page = PAGE_TEMPLATE.format(
            name=html.escape(name),
            home="../../index.html",
            docs=docs_html,
            year=datetime.date.today().year,
        )
        with open(os.path.join(OUT_DIR, tok + ".html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        links.append((code, name, tok, "courses/s/%s.html" % tok))
        print("✓ %s -> courses/s/%s.html" % (name, tok))
    with open(LINKS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "token", "page_path"])
        for code, name, tok, path in links:
            w.writerow([code, name, tok, path])
    print("\n共生成 %d 个学员页。" % len(links))
    print("私发对照表已写入 student_links.csv（请勿公开 / 请勿部署）。")
    print("部署后完整链接 = 你的站点域名 + page_path，例如 https://chucktian.com/courses/s/%s.html" % ("xxxx"))


if __name__ == "__main__":
    main()
