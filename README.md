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

## 六、学员专属页（Tier 2 · 每学员独立不可猜页面）
**为什么这样做**：纯静态站没有后端，做不了安全的"用户名+密码"认证（凭据会暴露在前端源码）。
本方案用「独立、随机、不可猜测的页面地址 + 微信私发」实现每学员内容隔离，且保持你自有品牌站。

**步骤**：
1. 编辑 `_admin/students.csv`，每行一个学员：
   ```
   code,name,doc
   alice,Alice 王同学,https://docs.qq.com/slide/你的嵌入链接
   ```
   - `doc` 填腾讯文档「分享 → 嵌入」拿到的 `<iframe src="...">` 或 直接链接；多个讲义用 `|` 分隔。
2. 运行：
   ```bash
   cd opc-site/_admin
   python generate_student_pages.py
   ```
3. 产出：
   - `courses/s/<token>.html` —— 每位学员一页，只含他自己的讲义（腾讯文档 iframe 嵌入）。
   - `student_links.csv` —— 本地私发对照表（**已被 .gitignore 忽略，勿公开**）。
4. 把 `student_links.csv` 里每位学员的页面路径，拼上你的站点域名，通过微信单独发给他。
   例如：`https://chucktian.com/courses/s/a1b2c3d4.html`

**要点**：
- 学员页地址随机不可猜，且每页只显示该学员内容 → 天然隔离。
- 真正的访问权限由**腾讯文档的「仅指定人 / 链接可看」**控制；页面地址只是入口。
- 新增 / 调整学员：改 `students.csv` 重跑脚本即可（旧 token 页可保留或手动删除）。
