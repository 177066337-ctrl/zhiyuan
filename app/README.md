# 高考志愿填报辅助工具 MVP

基于当前结构化院校和专业数据构建的基础检索型网页。

当前支持：

- 首页数据概览
- 院校查询与详情
- 专业查询与详情
- 本地收藏
- 数据说明页
- 志愿推荐占位页

当前不支持：

- 冲稳保推荐
- 录取概率
- 历年最低分 / 最低位次
- 招生计划
- 一分一段换算
- 登录、后端、数据库

本地运行：

```powershell
cd D:\2026\zhiyuan\app
npm install
npm run dev
```

构建：

```powershell
cd D:\2026\zhiyuan\app
npm run build
```

数据文件：

- `public/data/schools.enriched.json`：院校主数据
- `public/data/majors.json`：专业主数据
- `public/data/school_tags.json`：院校标签数据

GitHub Pages：

- 使用 `HashRouter`，避免静态托管环境下的刷新 404。
- `vite.config.ts` 支持通过 `VITE_BASE` 或兼容变量 `VITE_PUBLIC_BASE` 配置打包 `base`。
- 仓库页部署通常使用 `/zhiyuan/` 这类路径。
- 用户主页仓库通常使用 `/`。
