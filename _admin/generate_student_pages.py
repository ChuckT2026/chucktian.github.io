#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学员页生成器 v3 (统一登录页 + 账号 + 密码 + 半年有效期)
=====================================================
适用：Chuck 的商科 / 咨询课。每位学员获得一个独立「账号 + 密码」，
登录后即可在半年内免费反复查看专属讲义（PPT / PDF，由腾讯文档嵌入）。

重要：纯静态站（GitHub Pages）没有后端，无法做真正的服务端认证。
本脚本的「账号 + 密码」登录是前端校验（密码以 base64 混淆存于页面，
并非加密）。它提供的是「门槛 + 品牌体验」，真正的访问权限须由
腾讯文档的「仅指定人 / 链接+密码」来兜底。两者叠加即为可用方案。

v3 新增：courses/login.html 统一登录页
  - 学员在一个页面输入「账号 + 密码」，校验通过后自动跳转到各自专属页
  - 通过 sessionStorage 标记，跳转到专属页后不会再要求二次输密码
  - 专属页也保留独立密码门：直接拿到专属链接访问时，仍需输密码

用法：
  1) 编辑本目录 students.csv，每行一个学员：
     username,name,password,doc
     - username：账号（必填，英文/数字/下划线，作为页面名，自动转小写）
     - name：显示名（必填）
     - password：留空则自动生成 8 位密码；也可自定（如 20260923）
     - doc：腾讯文档「分享 → 嵌入」拿到的 <iframe src="..."> 或 直接链接；
            多个讲义用 | 分隔；留空则显示「讲义待上传」
  2) 运行：  python generate_student_pages.py
  3) 产出：
     - ../courses/s/<username>.html   每位学员一页（账号即页面路径）
     - ../courses/login.html          统一登录页（账号+密码 → 跳专属页）
     - student_links.csv             私发对照表（账号/密码/链接/有效期，
                                      已被 .gitignore 忽略，勿公开/勿部署）
依赖：仅 Python 3 标准库。
"""
import csv, os, re, secrets, string, base64, html, datetime, calendar

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "courses", "s")
LOGIN_PATH = os.path.join(HERE, "..", "courses", "login.html")
LINKS_CSV = os.path.join(HERE, "student_links.csv")
STUDENTS_CSV = os.path.join(HERE, "students.csv")
SITE_BASE = "https://chucktian.com"  # 部署后拼接用

PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{name} · 专属讲义 | Chuck Tian</title>
<style>
  :root{{--navy:#0E2240;--accent:#2D6CDF;--bg:#F5F8FC;--ink:#1B2533;--muted:#5A6678;--line:#E3E9F2}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}}
  a{{color:var(--accent);text-decoration:none}}
  .brand{{font-weight:700;color:var(--navy);letter-spacing:.3px}}
  .brand span{{color:var(--accent)}}
  .gate{{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0E2240,#15315C);padding:20px}}
  .login{{background:#fff;border-radius:16px;padding:34px 30px;width:100%;max-width:380px;box-shadow:0 10px 40px rgba(0,0,0,.25)}}
  .login .brand{{font-size:20px;margin-bottom:14px}}
  .login h1{{font-size:22px;color:var(--navy);margin-bottom:6px}}
  .login p{{font-size:13px;color:var(--muted);margin-bottom:18px}}
  .row{{margin-bottom:14px}}
  .row label{{display:block;font-size:13px;font-weight:700;color:var(--navy);margin-bottom:6px}}
  .row input{{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:9px;font-size:15px;outline:none}}
  .row input:focus{{border-color:var(--accent)}}
  .login button{{width:100%;padding:12px;background:var(--accent);color:#fff;border:0;border-radius:9px;font-size:15px;font-weight:700;cursor:pointer}}
  .login button:hover{{background:#1E50B5}}
  .err{{color:#c0392b;font-size:13px;margin-top:10px;min-height:18px}}
  .back{{display:inline-block;margin-top:16px;font-size:13px;color:var(--muted)}}
  .nav{{background:var(--navy);padding:16px 22px;display:flex;align-items:center;justify-content:space-between}}
  .nav .brand{{color:#fff}}
  .nav .brand span{{color:#9fc2f5}}
  .nav a{{color:#cfe0f7;font-size:14px;font-weight:600}}
  .wrap{{max-width:1000px;margin:0 auto;padding:0 20px}}
  .hero{{background:var(--navy);color:#fff;padding:40px 0 34px}}
  .hero h1{{font-size:26px;margin:8px 0 6px;color:#fff}}
  .hero p{{color:rgba(255,255,255,.82);font-size:14px}}
  .badge{{display:inline-block;font-size:12px;font-weight:700;color:var(--accent);background:#E8F0FC;border-radius:6px;padding:3px 10px}}
  .expiry{{display:inline-block;margin-top:10px;font-size:12px;color:#9fc2f5;background:rgba(255,255,255,.1);border-radius:6px;padding:4px 10px}}
  section{{padding:30px 0}}
  .doc{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(20,40,80,.04)}}
  .doc h3{{color:var(--navy);font-size:17px;margin-bottom:4px}}
  .doc .meta{{font-size:12px;color:var(--muted);margin-bottom:12px}}
  .frame{{position:relative;width:100%;padding-top:75%;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fafcff}}
  .frame iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:0}}
  .pending{{background:#fbf0e3;border:1px solid #f0d9bf;color:#8a5a1e;border-radius:10px;padding:16px;font-size:14px}}
  .warn{{background:#fbf0e3;border:1px solid #f0d9bf;color:#8a5a1e;border-radius:10px;padding:12px 14px;font-size:13px;margin-top:6px}}
  footer{{text-align:center;color:var(--muted);font-size:12px;padding:26px 0}}
</style>
</head>
<body>
<div class="gate" id="gate">
  <div class="login">
    <div class="brand">Chuck Tian</div>
    <h1>学员登录</h1>
    <p>请输入你的账号与密码，进入专属讲义。</p>
    <div class="row"><label>账号</label><input id="u" value="{username}" readonly></div>
    <div class="row"><label>密码</label><input id="p" type="password" placeholder="请输入密码" autocomplete="off"></div>
    <button onclick="check()">进入讲义</button>
    <div class="err" id="err"></div>
    <a class="back" href="{home}">← 返回首页</a>
  </div>
</div>
<div id="content" style="display:none">
  <div class="nav"><div class="brand">Chuck Tian</div><a href="{home}">← 返回首页</a></div>
  <section class="hero"><div class="wrap">
    <span class="badge">STUDENT ZONE · 专属讲义</span>
    <h1>{name}，这是你的专属讲义页</h1>
    <p>本页只显示你本人的课程讲义，请在半年有效期内免费反复查看。</p>
    <span class="expiry">有效期至 {expiry}（半年免费复看）</span>
  </div></section>
  <section><div class="wrap">
{docs}
    <div class="warn">提示：讲义由腾讯文档嵌入展示。如显示「无权限」，说明 Chuck 尚未为你开通该文档的查看权限，请微信联系 Chuck 开通。</div>
  </div></section>
  <footer>© {year} Chuck Tian · AI &amp; Strategy OPC · 专属内容，仅供本人查看</footer>
</div>
<script>
var ACC = "{username}";
var PW = "{pw}";
function show(){{ document.getElementById('gate').style.display='none'; document.getElementById('content').style.display='block'; }}
function check(){{
  var u = document.getElementById('u').value.trim();
  var p = document.getElementById('p').value;
  var err = document.getElementById('err');
  if(u !== ACC){{ err.textContent = '账号不正确'; return; }}
  if(btoa(unescape(encodeURIComponent(p))) !== PW){{ err.textContent = '密码不正确'; return; }}
  try{{ sessionStorage.setItem('auth_'+ACC, '1'); }}catch(e){{}}
  show();
}}
try{{ if(sessionStorage.getItem('auth_'+ACC) === '1'){{ show(); }} }}catch(e){{}}
</script>
</body>
</html>"""

LOGIN_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>学员登录 | Chuck Tian</title>
<style>
  :root{{--navy:#0E2240;--accent:#2D6CDF;--bg:#F5F8FC;--ink:#1B2533;--muted:#5A6678;--line:#E3E9F2}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}}
  a{{color:var(--accent);text-decoration:none}}
  .brand{{font-weight:700;color:var(--navy);letter-spacing:.3px}}
  .brand span{{color:var(--accent)}}
  .gate{{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0E2240,#15315C);padding:20px}}
  .login{{background:#fff;border-radius:16px;padding:34px 30px;width:100%;max-width:380px;box-shadow:0 10px 40px rgba(0,0,0,.25)}}
  .login .brand{{font-size:20px;margin-bottom:14px}}
  .login h1{{font-size:22px;color:var(--navy);margin-bottom:6px}}
  .login p{{font-size:13px;color:var(--muted);margin-bottom:18px}}
  .row{{margin-bottom:14px}}
  .row label{{display:block;font-size:13px;font-weight:700;color:var(--navy);margin-bottom:6px}}
  .row input{{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:9px;font-size:15px;outline:none}}
  .row input:focus{{border-color:var(--accent)}}
  .login button{{width:100%;padding:12px;background:var(--accent);color:#fff;border:0;border-radius:9px;font-size:15px;font-weight:700;cursor:pointer}}
  .login button:hover{{background:#1E50B5}}
  .err{{color:#c0392b;font-size:13px;margin-top:10px;min-height:18px}}
  .back{{display:inline-block;margin-top:16px;font-size:13px;color:var(--muted)}}
</style>
</head>
<body>
<div class="gate"><div class="login">
  <div class="brand">Chuck Tian</div>
  <h1>学员登录</h1>
  <p>请输入你的账号与密码，进入专属讲义。</p>
  <div class="row"><label>账号</label><input id="u" placeholder="请输入账号" autocomplete="off"></div>
  <div class="row"><label>密码</label><input id="p" type="password" placeholder="请输入密码" autocomplete="off"></div>
  <button onclick="login()">进入讲义</button>
  <div class="err" id="err"></div>
  <a class="back" href="../index.html">← 返回首页</a>
</div></div>
<script>
var USERS = {{{usermap}}};
function login(){{
  var u = document.getElementById('u').value.trim().toLowerCase();
  var p = document.getElementById('p').value;
  var err = document.getElementById('err');
  if(!(u in USERS)){{ err.textContent = '账号不存在'; return; }}
  if(btoa(unescape(encodeURIComponent(p))) !== USERS[u]){{ err.textContent = '密码不正确'; return; }}
  try{{ sessionStorage.setItem('auth_'+u, '1'); }}catch(e){{}}
  location.href = 's/' + u + '.html';
}}
</script>
</body>
</html>"""

DOC_TEMPLATE = """  <div class="doc">
    <h3>{title}</h3>
    <div class="meta">腾讯文档 · 点击右上角可全屏 / 下载</div>
    <div class="frame"><iframe src="{src}" allowfullscreen></iframe></div>
  </div>"""

PENDING_TEMPLATE = """  <div class="pending">讲义即将上传，敬请期待。Chuck 上传后本页会自动更新，你可在有效期内随时回看。</div>"""


def extract_src(cell):
    cell = (cell or "").strip()
    if not cell:
        return None
    if "<iframe" in cell.lower():
        m = re.search(r'src=["\']([^"\']+)["\']', cell, re.I)
        return m.group(1) if m else None
    return cell


def gen_password(n=8):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def b64(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def sanitize_username(u):
    u = (u or "").strip().lower()
    u = re.sub(r"[^a-z0-9_]", "_", u)
    return u


def add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    last = calendar.monthrange(y, m)[1]
    return datetime.date(y, m, min(d.day, last))


def main():
    if not os.path.exists(STUDENTS_CSV):
        print("未找到 students.csv，请先创建。")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    with open(STUDENTS_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    links = []
    user_entries = []  # (username, b64pw) for login page
    today = datetime.date.today()
    for r in rows:
        username = sanitize_username(r.get("username"))
        name = (r.get("name") or "").strip()
        pw_in = (r.get("password") or "").strip()
        docs_raw = (r.get("doc") or "").strip()
        if not username or not name:
            print("· 跳过：缺少 username 或 name 的行")
            continue
        password = pw_in if pw_in else gen_password()
        srcs = [extract_src(x) for x in docs_raw.split("|")]
        srcs = [s for s in srcs if s]
        if srcs:
            docs_html = ""
            for i, s in enumerate(srcs, 1):
                docs_html += DOC_TEMPLATE.format(title="讲义 %d" % i, src=html.escape(s, quote=True))
        else:
            docs_html = PENDING_TEMPLATE
        expiry = add_months(today, 6)
        page = PAGE_TEMPLATE.format(
            username=html.escape(username),
            name=html.escape(name),
            pw=b64(password),
            home="../../index.html",
            expiry=expiry.isoformat(),
            docs=docs_html,
            year=today.year,
        )
        out = os.path.join(OUT_DIR, username + ".html")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(page)
        links.append((username, name, password, "courses/s/%s.html" % username, expiry.isoformat()))
        user_entries.append((username, b64(password)))
        print("✓ %s (%s) -> courses/s/%s.html" % (name, username, username))

    # 统一登录页
    usermap = ", ".join('"%s":"%s"' % (u, p) for u, p in user_entries)
    login_html = LOGIN_TEMPLATE.format(usermap=usermap)
    with open(LOGIN_PATH, "w", encoding="utf-8") as fh:
        fh.write(login_html)
    print("✓ 统一登录页 -> courses/login.html")

    with open(LINKS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["username", "name", "password", "page_path", "expiry"])
        for u, n, p, path, exp in links:
            w.writerow([u, n, p, path, exp])
    print("\n共生成 %d 个学员页。" % len(links))
    print("私发对照表 -> student_links.csv（含账号/密码/有效期，已被 .gitignore 忽略，勿公开）")
    print("统一登录页 -> %s/courses/login.html" % SITE_BASE)
    print("部署后学员链接 = %s/courses/s/<账号>.html" % SITE_BASE)
    if links:
        print("\n--- 生成的账号 / 密码（也见 student_links.csv）---")
        for u, n, p, path, exp in links:
            print("  账号 %-12s 密码 %-10s 有效期 %s" % (u, p, exp))


if __name__ == "__main__":
    main()
