# Chuck Tian · OPC 官网（静态单页）

自包含静态站，可直接部署到 GitHub Pages / Vercel / 腾讯云 CloudBase。
**设计**：Light 主题，深海军蓝 `#0E2240` + 蓝 `#2D6CDF`，自包含、无构建步骤。

---

## 目录结构
```
opc-site/
├─ index.html              # 首页（Hero / 你能得到什么 / 服务套餐 / 学员专区 / 关于 / 联系）
├─ CNAME                   # 自定义域名（仅自定义域名模式需要）
├─ .gitignore              # 忽略私发对照表
└─ _admin/                 # 构建脚本（不对外展示内容）
   ├─ generate_student_pages.py   # 学员专属页生成器
   ├─ students.csv                # 学员清单（输入）
   └─ student_links.csv           # 私发对照表（输出，已被 .gitignore 忽略）
```

---

## 一、本地预览
直接用浏览器打开 `index.html` 即可。

## 二、上线前必做（替换占位符）
打开 `index.html`，搜索替换：
- `[LinkedIn链接]` → 你的 LinkedIn 主页
- `[微信号]` → 你的微信 / 企微
- `[邮箱]` → 你的邮箱
- `关于我` 区的 `<div class="portrait">` 里放一张职业照

---

## 三、部署方式 A：免费子域（推荐先用这个）
GitHub Pages 给每个账号一个**免费域名**：`你的用户名.github.io`，无需购买任何东西。

```bash
cd opc-site
# ⚠️ 免费子域模式请先删除本目录下的 CNAME 文件（否则会强制跳转 chucktian.com 导致打不开）
git init
git add .
git commit -m "OPC site v1"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```
仓库 **Settings → Pages → Source** 选 `main` / `/root`，等待 1–2 分钟。
你的站点地址：`https://<你的用户名>.github.io/<仓库名>/`（仓库名建议叫 `opc-site` 或 `<用户名>.github.io`）。

## 四、部署方式 B：自定义域名 chucktian.com（对外更专业）
1. 在腾讯云 / 阿里云购买 `chucktian.com`（约 ¥83/年，确认可注册后购买）。
2. 本目录 `CNAME` 已写 `chucktian.com`，**保留它**。
3. 域名 DNS 加一条 CNAME：`@` → `<你的用户名>.github.io`。
4. GitHub 仓库 **Settings → Pages → Custom domain** 填 `chucktian.com`，等待生效。
> 买了域名后**无需重建网站**，只是指向变了；两种方式站点文件完全相同。

## 五、部署到 Vercel / 腾讯云 CloudBase（可选）
- Vercel：把 `opc-site` 作为项目根目录直接导入，零配置。
- CloudBase：`tcb hosting deploy ./ chucktian`（需先 `npm i -g @cloudbase/cli && tcb login`）。

---

## 六、学员专区（统一登录页 + 账号 + 密码 + 半年有效期）
**目标**：每位在读学员获得独立「账号 + 密码」，登录后在半年内免费反复查看专属讲义（PPT / PDF）。

**学员怎么登录（v3）**：
- 统一入口：`https://chucktian.com/courses/login.html` —— 输入「账号 + 密码」→ 自动跳到他的专属页。
- 专属页：`https://chucktian.com/courses/s/<账号>.html` —— 直接拿到链接访问时，仍需输密码（独立密码门）。
- 首页「学员专区」的「学员登录入口」按钮也指向 `courses/login.html`。

**架构说明（务必读）**：纯静态站（GitHub Pages）没有后端，无法做真正的服务端认证。
本方案的「账号 + 密码」登录是**前端校验**（密码以 base64 混淆存于页面，并非加密）。
它提供的是「门槛 + 品牌体验」；**真正的访问权限须由腾讯文档的「仅指定人 / 链接+密码」兜底**。
两层叠加即为可用方案：
- 第一层：不可猜测的页面名（账号即页面路径）+ 前端密码门 + 统一登录页
- 第二层（关键）：讲义以腾讯文档嵌入，文档本身设「仅指定人 / 链接+密码」查看

**步骤**：
1. 编辑 `_admin/students.csv`，每行一个学员：
   ```
   username,name,password,doc
   zhuxinyi,Zhuxinyi,20260923,https://docs.qq.com/slide/你的嵌入链接
   ```
   - `username`：账号（必填，英文/数字/下划线，作为页面名，自动转小写）
   - `name`：显示名（必填）
   - `password`：留空则自动生成 8 位密码；也可自定（如 20260923）
   - `doc`：腾讯文档「分享 → 嵌入」拿到的 `<iframe src="...">` 或 直接链接；多个讲义用 `|` 分隔；留空则显示「讲义待上传」
2. 运行（需本机装有 Python 3）：
   ```bash
   cd opc-site/_admin
   python generate_student_pages.py
   ```
3. 产出：
   - `courses/login.html` —— 统一登录页（账号+密码 → 跳专属页）。
   - `courses/s/<username>.html` —— 每位学员一页（账号即页面路径），含登录门 + 专属讲义（腾讯文档 iframe）。
   - `student_links.csv` —— 账号/密码/链接/有效期对照表（**已被 .gitignore 忽略，含密码，严禁公开/严禁部署**）。
4. 把每位学员的**账号、密码**，通过微信单独发给他；让他访问 `https://chucktian.com/courses/login.html` 登录即可（无需发专属页链接）。
5. 上传讲义：把该学员的 PPT / PDF 传到腾讯文档 → 分享 → 嵌入 → 复制 `<iframe src>` 填回 `students.csv` 的 `doc` 列（多个用 `|` 分隔）→ 重跑脚本即可更新。

**要点**：
- 学员页 + 登录页随站点一起部署（`courses/` 不再被 gitignore 忽略），否则学生打不开。
- `student_links.csv` 含明文密码，**务必保留在本地、不要 commit / 不要公开**。
- 半年有效期在页面展示并由你人工管理：到期后可删页或改密码（在 students.csv 改完重跑）。
- 新增 / 调整学员：改 `students.csv` 重跑脚本；旧页可保留或手动删除。
