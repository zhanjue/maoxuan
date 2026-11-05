#!/usr/bin/env bash
# 把 site/ 直传到 Cloudflare Pages（不需要 Git，不需要构建）。
#
# 首次准备（只做一次）：
#   npm i -g wrangler
#   wrangler login
#
# 之后每次更新：
#   1) python scripts/build.py
#   2) bash deploy-cf.sh
#
# 项目名固定，重复执行就是覆盖发布，地址不变。

set -euo pipefail
cd "$(dirname "$0")"

PROJECT="maoxuan"

[ -f site/index.html ] || { echo "site/index.html 不存在，先跑 python scripts/build.py"; exit 1; }

command -v wrangler >/dev/null 2>&1 || { echo "没装 wrangler：npm i -g wrangler"; exit 1; }

echo "上传 site/ -> Cloudflare Pages 项目 ${PROJECT} ..."
wrangler pages deploy site --project-name="$PROJECT" --commit-dirty=true
