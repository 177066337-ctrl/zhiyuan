# GitHub 上传检查清单

## 上传前先检查

1. 当前前端项目入口在 `D:\2026\zhiyuan\app`
2. 网页运行依赖的是 `app/public/data/` 下的 JSON 文件
3. 根目录散落着大量 PDF、Word、Excel、PPT 原始资料，这些文件默认不建议公开上传
4. `node_modules`、`app/dist`、日志和缓存文件不应提交

## 建议提交的文件

- `AGENTS.md`
- `README.md`
- `.gitignore`
- `.github/workflows/deploy.yml`
- `app/package.json`
- `app/package-lock.json`
- `app/index.html`
- `app/vite.config.ts`
- `app/tsconfig.json`
- `app/tailwind.config.js`
- `app/postcss.config.js`
- `app/src/`
- `app/public/data/schools.enriched.json`
- `app/public/data/majors.json`
- `app/public/data/school_tags.json`
- `scripts/`
- `docs/`

## 不应该提交的文件

- `node_modules/`
- `app/node_modules/`
- `app/dist/`
- `app/dist/dist-server.log`
- `raw_data/`
- `*.log`
- `*.tmp`
- `*.tsbuildinfo`
- `.vscode/`
- `.idea/`
- 根目录散落的原始 PDF / Word / Excel / PPT 资料

## 根目录散落原始资料的提醒

当前项目没有把原始资料统一放进 `raw_data/`，而是直接散落在根目录。因此上传前不要直接执行无差别的 `git add .`。

更稳妥的做法是：

1. 先看 `git status`
2. 只添加需要公开的文件和目录
3. 再次确认没有把原始资料加入暂存区

## 如何创建 GitHub 仓库

1. 登录 GitHub
2. 点击右上角 `New repository`
3. 仓库名填写 `zhiyuan`，或你自己的目标仓库名
4. 建议先创建空仓库，不勾选自动生成 README、`.gitignore` 或 license

## Windows PowerShell 本地初始化 Git

把下面命令中的 `你的用户名` 替换成你自己的 GitHub 用户名：

```powershell
cd D:\2026\zhiyuan
git init
git branch -M main
git add AGENTS.md
git add README.md
git add .gitignore
git add .github\workflows\deploy.yml
git add app
git add scripts
git add docs
git status
git commit -m "Initial MVP for gaokao volunteer helper"
git remote add origin https://github.com/你的用户名/zhiyuan.git
git push -u origin main
```

## 如果你坚持用 `git add .`

先确保：

1. `.gitignore` 已存在
2. `app/dist/` 已被忽略
3. `node_modules/` 已被忽略
4. 根目录散落原始资料没有被误加入

然后一定要执行：

```powershell
git status
```

如果看到大量 PDF / DOC / DOCX / XLS / XLSX / PPT / PPTX 出现在待提交列表中，不要提交，先用 `git restore --staged <文件名>` 逐个撤出暂存区。

## 如何开启 GitHub Pages

1. 进入 GitHub 仓库页面
2. 打开 `Settings`
3. 进入 `Pages`
4. 在 `Source` 中选择 `GitHub Actions`
5. 推送到 `main` 后等待 Actions 自动部署

## 如何查看 GitHub Actions 部署结果

1. 打开仓库的 `Actions`
2. 查看最新一次 `Deploy GitHub Pages`
3. 先确认 `build` 成功，再确认 `deploy` 成功
4. 成功后在 `Pages` 页面或 Actions 输出中查看站点地址

## 如何排查白屏

1. 检查 `app/vite.config.ts` 的 `base` 是否和仓库路径一致
2. 仓库名是 `zhiyuan` 时，应使用 `/zhiyuan/`
3. 用户主页仓库应使用 `/`
4. 检查浏览器控制台是否请求了错误的 JS、CSS 或 JSON 路径

## 如何排查 404

1. 确认 GitHub Pages 来源是 `GitHub Actions`
2. 确认 workflow 上传的是 `app/dist`
3. 确认访问地址是否带正确仓库前缀
4. 本项目使用 `HashRouter`，正常情况下刷新子页面不应触发 404

## 如何排查数据加载失败

1. 检查 `app/public/data/` 中是否包含：
   `schools.enriched.json`
   `majors.json`
   `school_tags.json`
2. 检查构建后 `app/dist/data/` 是否存在这些 JSON 文件
3. 打开浏览器开发者工具查看 Network 面板，确认 JSON 请求没有 404
4. 如果部署路径变化，先检查 `base` 配置是否正确

## 本地构建锁文件问题

如果 `npm run build` 报错并指向 `app/dist/dist-server.log`：

1. 说明有进程仍在占用 `app/dist`
2. 先关闭本地预览服务器、相关终端和编辑器
3. 再手动删除 `app/dist`
4. 然后重新执行：

```powershell
cd D:\2026\zhiyuan\app
npm run build
```
