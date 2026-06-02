# 部署说明

## 本地运行

```powershell
cd D:\2026\zhiyuan\app
npm install
npm run dev
```

## 本地打包

```powershell
cd D:\2026\zhiyuan\app
npm run build
```

如果本机曾出现 `app/dist/dist-server.log` 被占用的问题，先关闭占用该文件的预览进程、终端或编辑器，再删除 `app/dist/` 后重新构建。

## GitHub Pages 的 `base` 配置

当前项目在 [vite.config.ts](D:/2026/zhiyuan/app/vite.config.ts) 中优先读取 `VITE_BASE`，同时兼容 `VITE_PUBLIC_BASE`：

- 本地开发默认使用 `/`
- 仓库页部署，例如仓库名为 `zhiyuan`，应使用 `/zhiyuan/`
- 用户主页仓库，例如 `username.github.io`，应使用 `/`

示例：

```powershell
$env:VITE_BASE="/zhiyuan/"
npm run build
```

如果要部署到用户主页仓库：

```powershell
$env:VITE_BASE="/"
npm run build
```

## GitHub Actions 工作流

当前工作流文件为 [deploy.yml](D:/2026/zhiyuan/.github/workflows/deploy.yml)，已配置：

- `push` 到 `main` / `master` 时触发
- 在 `app/` 目录执行 `npm install`
- 在 `app/` 目录执行 `npm run build`
- 上传 `app/dist` 为 Pages artifact
- 使用官方 Pages Actions 部署
- 含 `pages: write` 与 `id-token: write` 权限
- 默认以 `VITE_BASE=/zhiyuan/` 进行仓库页部署

## 开启 GitHub Pages

1. 打开仓库 `Settings`
2. 进入 `Pages`
3. 将 `Source` 设置为 `GitHub Actions`
4. 推送代码后等待 Actions 工作流完成发布

## 页面空白时如何检查

1. 检查 `vite.config.ts` 中的 `base` 是否与仓库路径一致。
2. 检查浏览器控制台是否请求了错误的静态资源路径。
3. 确认 `schools.enriched.json`、`majors.json`、`school_tags.json` 都在 `app/public/data/`。

## 404 时如何检查

本项目使用 `HashRouter`，正常情况下静态托管不应因路由刷新触发 404。

如果仍然出现问题，优先检查：

1. GitHub Pages 是否已切换到 `GitHub Actions`
2. workflow 是否成功发布了 `app/dist`
3. 页面访问地址是否带有正确仓库前缀
