# Final Deployment Check

## Build

- `npm.cmd run build` 成功
- `app/dist` 已正常生成
- PowerShell 直接调用 `npm` 会受本机执行策略影响，建议本地使用 `npm.cmd`

## GitHub Pages Base

- 线上地址：`https://177066337-ctrl.github.io/zhiyuan/`
- [vite.config.ts](/D:/2026/zhiyuan/app/vite.config.ts) 已支持通过 `VITE_BASE` 注入 base
- [.github/workflows/deploy.yml](/D:/2026/zhiyuan/.github/workflows/deploy.yml) 当前使用 `VITE_BASE: /zhiyuan/`
- 结论：GitHub Pages 的 base 配置正确

## Router And Refresh

- 路由使用的是 `createHashRouter`
- 页面路径为 `#/score-lookup`、`#/schools`、`#/majors`
- GitHub Pages 刷新不会触发服务端 404
- 当前不依赖额外的 `404.html` fallback

## Workflow

- 触发分支：`main` / `master`
- 工作目录：`app`
- 安装依赖：`npm install`
- 构建命令：`npm run build`
- 上传制品：`app/dist`
- 部署动作：官方 GitHub Pages Actions
- 结论：workflow 配置正确

## Data Package Checks

- `app/public/data/score-lookup` 仅包含前端候选分片、`index.json`、`coverage.json`
- 未发现 `data_work`
- 未发现 16G 原始资料目录
- 未发现原始 PDF / Excel / Word / PPT

## Dist Package Checks

- `app/dist` 体积：`147.79 MB`
- 未发现 `data_work`
- 未发现 `高考志Y系列资料`
- 未发现原始 PDF / Excel / Word / PPT

## Current Sizes

- `app/public/data/score-lookup`：`144.07 MB`
- `app/dist`：`147.79 MB`

## Git Ignore Checks

- 已排除：
  - `data_work/`
  - `高考志Y系列资料/`
  - `node_modules/`
  - `app/node_modules/`
  - `app/dist/`
  - 各类抽取 raw / normalized / backfill 目录
  - 日志和临时文件
  - 根目录原始 PDF / Excel / Word / PPT

## Conclusion

- 当前版本可以 push 到 GitHub 并部署 GitHub Pages
- 发布定位仍应保持：
  - “全国候选试验版”
  - “历史参考，不构成录取承诺”
