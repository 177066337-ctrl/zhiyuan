# Score Lookup Release Checklist

- 前端公开候选数据集：88 个
- verified：2
- warning：3
- candidate：7
- score_only：76
- coverage 组合：55
- admissions 分片文件：272
- rank_table 分片文件：8
- JSON 缺失文件：0
- JSON 解析错误：0
- 风险禁用词命中：0
- 风险说明关键词命中：3

## 发布前检查

- 福建 2023 历史类仍保持“已抽检通过”
- 江西 2025 历史类仍保持“抽检发现问题，谨慎参考”
- 新增 `candidate` 已展示“未人工复核”
- 无 rank_table 的数据集仍降级为“仅分数参考”
- 页面未出现“录取概率”“稳录”“保证录取”等承诺性话术
- 首页和 `/score-lookup` 仍是按需加载，没有把 admissions 全量灌入初始页面
- `app/dist` 未包含 `data_work`
- `app/dist` 未包含 16G 原始资料

## 结论

- 当前版本可以部署
- 但部署定位仍应明确为“全国候选试验版”
- 后续任何扩大开放的动作，都应优先补 `rank_table` 和人工复核，不应先做推荐算法
