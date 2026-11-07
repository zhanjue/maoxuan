# 部署说明

这个仓库根目录是**源数据 + 构建脚本**，对外发布的只有 `site/` 一个目录。
`data/`、`scripts/` 不用上传到任何托管平台，只用于本地重建。

三条命令就能更新线上：

```bash
python scripts/build.py          # 改完 data/ 或 build.py 后重建 site/
git add -A && git commit -m "..." && git push    # 触发 GitHub Pages 自动发布
bash deploy-cf.sh                # 需要时另外推一份到 Cloudflare Pages
```

---

## 〇、本地怎么"启动"

**最省事**：直接双击 `site\index.html`。全站数据内联，`file://` 就能打开，不需要服务。

**要网址（推荐）**：双击根目录的 **`启动预览.bat`** —— 自动起本地服务并打开
`http://127.0.0.1:8801/index.html`。关掉那个黑窗口就停止。服务已在跑时会直接开浏览器。

手动等价命令：

```bat
cd /d E:\software\agent\workbuddy_workplcae\mao-kb
"C:\Users\80926\.workbuddy\binaries\python\versions\3.13.12\python.exe" _serve.py 8801
```

`_serve.py` 带了 `Cache-Control: no-store`，改完重建刷新就能看到新版；
如果还看到旧页面，按 `Ctrl+Shift+R` 硬刷新，或者换一个端口重开（`_serve.py 8802`）。

---

## 一、GitHub Pages

### 一次性配置

1. 建仓库（免费账号用 Pages 建议公开仓库）
2. 推送 `main` 分支
3. **仓库 Settings → Pages → Build and deployment → Source 选 GitHub Actions**
   —— 这一步必须在网页上点一次，没有 API 可替代。**没做的表现**：工作流在
   `Setup Pages` 那一步失败（`Get Pages site failed / Not Found`），后面的
   Upload、Deploy 全被跳过。点完再在 Actions 里 `Re-run all jobs` 即可。
4. 之后每次 push 到 `main` 且 `site/` 有变化，`.github/workflows/pages.yml` 会自动发布

### 地址

| 仓库名 | 访问地址 |
|---|---|
| `<用户名>.github.io` | `https://<用户名>.github.io/` |
| 其他名字（如 `maoxuan`） | `https://<用户名>.github.io/maoxuan/` |

**当前仓库 `zhanjue/maoxuan`，站点地址 `https://zhanjue.github.io/maoxuan/`。**
2026-11-07 从 `maoxuan1` 改名而来 —— **Pages 的子路径就是仓库名**，想让地址不带「1」只能改仓库名（在仓库 Settings 里改，改名后 `git remote` 也要跟着换）。旧地址 `github.io/maoxuan1/` 会自动 301 到新地址，但对外只用新的。

**本站所有链接都是相对路径**，放在子路径下也能正常工作，不需要改配置。

### 注意

- 第一次发布要等 1~2 分钟，Actions 页面能看到进度
- 如果 404，先看 Actions 是不是红的；最常见原因是 `site/index.html` 没提交（工作流会提前报错拦住）
- 国内访问 `github.io` 经常很慢或打不开，**不建议当主要对外地址**

---

## 二、Cloudflare Pages

### 为什么选它

免费、不需要备案（用 `pages.dev` 子域名）、国内访问比 `github.io` 稳一些、能绑自己的域名。
本站是纯静态，**不需要服务器、不需要数据库**，传上去就是全部。

### 一次性配置（要做的事只有两件：注册 + 授权）

1. **注册账号**：打开 <https://dash.cloudflare.com/sign-up>，邮箱 + 密码，去邮箱点验证链接。
   不需要绑卡，免费额度（每月 500 次构建、无限请求）够用。
2. **授权这台电脑**：双击根目录的 **`部署到Cloudflare.bat`**。第一次运行会自动下载
   `wrangler`（命令行工具，约 40MB），然后弹出浏览器让你登录 —— 选你那台机器上的
   Cloudflare 账号，点 **Allow**。这一步只做一次，凭据存在本机。

### 之后每次发布

改完内容，双击 **`部署到Cloudflare.bat`** 就行。它依次做三件事：
重新构建 → 检查登录（已登录自动跳过）→ 上传 `site/`。看到 `Deployment complete` 就成功了，
通常 10~30 秒生效。项目名固定是 `maoxuan1`，重复执行是覆盖，地址不变。

命令行等价写法：

```bash
npx wrangler pages deploy site --project-name=maoxuan1 --commit-dirty=true
```

### 地址

`https://maoxuan1.pages.dev` —— 项目名 `maoxuan1`，生产分支 `main`，短域名不带后缀。

**项目名的来历**：最早那个项目叫 `mao-kb`（域名 `mao-kb.pages.dev`，已停在旧内容）；
第二次用了 `maoxuan`，撞上别人已占的 `maoxuan.pages.dev`，Cloudflare 把域名自动加成
`maoxuan-cye.pages.dev`，项目已在 2026-11-06 删掉。现在是第三次，`maoxuan1.pages.dev`
没人占，域名就是项目名本身。以后改名之前，先在浏览器里试一下 `<名字>.pages.dev` 是否可注册。

页面会做 pretty URL：站内的 `concepts.html` 会被 308 到 `/concepts`，实际内容照常返回；
`concepts/`、`works/` 这类同名目录不冲突（`/concepts` 就是概念图谱页本身）。

### 注意

- **不要**用 Connect to Git 方式，那个方式默认把仓库根目录当站点，会发布不出东西。用直传。
- 第一次要在本机登录一次：`npx wrangler login`（浏览器里点 Allow，凭据存本机）。之后不用再登。
- 本机装了代理时 wrangler 会走代理，**上传偶尔在 16/49 或 32/49 处 `Failed to upload files`**，
  再执行一遍就好——它是整批重传，不会传坏。
- 如果要接 Git 自动部署，Build output directory 必须填 `site`，Build command 留空。
- `pages.dev` 在国内部分运营商下可能超时，长期用建议绑自定义域名。
- 想临时给别人看一眼、又不想注册账号：`npx wrangler pages deploy` 之外还有
  `cloudflared tunnel --url http://127.0.0.1:8801`（免登录，随机域名，关电脑就失效）。

---

## 三、换域名 / 迁到国内

`site/` 是完全可移植的静态文件，换平台就是重新上传一遍，**零改动**。

- Cloudflare Pages 绑自定义域名：Pages 项目 → Custom domains → 加域名 → 按提示改 DNS
- 迁到腾讯云 COS / 阿里云 OSS：开通静态网站托管，把 `site/` 里的内容（不是 `site` 文件夹本身）传到桶根目录
- 国内 + 自己的域名 = **必须备案**（3~4 周）。备案期间可以先用平台默认域名对外

### CDN 必做两项

用国内对象存储 + CDN 时，务必在控制台设置：

1. **流量告警 + 费用封顶** —— 静态站最容易被恶意刷流量刷出账单
2. **开访问日志** —— 这是最省事的访问统计，零代码

---

## 四、构建产物说明

`site/` 由 `scripts/build.py` 生成，不要手改 `site/` 里的文件（改了下次构建会被覆盖）。

样式缓存靠 `style.css?v=N` 的版本号控制，**改了 `site/assets/style.css` 必须在 `scripts/build.py`
里把版本号 +1 再重建**，否则访客浏览器会继续用旧样式。
