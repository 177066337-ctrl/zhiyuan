# 高考志愿填报辅助工具

项目根目录：`D:\2026\zhiyuan`

前端应用入口在 [app](D:/2026/zhiyuan/app/) 目录下，这是当前需要上传到 GitHub 并部署到 GitHub Pages 的核心部分。

当前 MVP 已支持：

- 院校查询
- 专业查询
- 985 / 211 / 双一流筛选
- 收藏与导出
- 数据说明页

当前不支持：

- 冲稳保推荐
- 录取概率
- 历年分数线 / 位次
- 招生计划
- 后端与登录系统

本地运行：

```powershell
cd D:\2026\zhiyuan\app
npm install
npm run dev
```

生产构建：

```powershell
cd D:\2026\zhiyuan\app
npm run build
```

部署相关说明见：

- [GitHub 上传检查清单](D:/2026/zhiyuan/docs/github_upload_checklist.md)
- [部署说明](D:/2026/zhiyuan/docs/deployment.md)

注意：

- `app/public/data/` 下的 JSON 文件是网页运行所需数据。
- 根目录散落的大量 PDF / Word / Excel / PPT 原始资料不建议直接公开上传。
