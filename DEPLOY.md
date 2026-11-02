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

## 一、GitHub Pages

### 一次性配置

1. 建仓库（建议私有或公开都行，Pages 用 Actions 发布不受仓库可见性限制）
2. 推送 `main` 分支
3. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**
4. 之后每次 push 到 `main` 且 `site/` 有变化，`.github/workflows/pages.yml` 会自动发布

### 地址

| 仓库名 | 访问地址 |
|---|---|
| `<用户名>.github.io` | `https://<用户名>.github.io/` |
| 其他名字（如 `mao-kb`） | `https://<用户名>.github.io/mao-kb/` |

**本站所有链接都是相对路径**，放在子路径下也能正常工作，不需要改配置。

### 注意

- 第一次发布要等 1~2 分钟，Actions 页面能看到进度
- 如果 404，先看 Actions 是不是红的；最常见原因是 `site/index.html` 没提交（工作流会提前报错拦住）
- 国内访问 `github.io` 经常很慢或打不开，**不建议当主要对外地址**

---

## 二、Cloudflare Pages

### 一次性配置

```bash
npm i -g wrangler
wrangler login          # 浏览器里点一次授权
```

### 发布

```bash
python scripts/build.py
bash deploy-cf.sh
```

脚本里的项目名是 `mao-kb`，第一次执行会自动创建项目，之后每次都是覆盖发布，地址不变。

### 地址

`https://mao-kb.pages.dev`

### 注意

- **不要**用 Connect to Git 方式，那个方式默认把仓库根目录当站点，会发布不出东西。用直传。
- 如果要接 Git 自动部署，Build output directory 必须填 `site`，Build command 留空。
- `pages.dev` 在国内部分运营商下可能超时，长期用建议绑自定义域名。

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
