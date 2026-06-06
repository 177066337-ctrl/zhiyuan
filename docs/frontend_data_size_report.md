# Frontend Data Size Report

- `app/public/data/score-lookup` 总体积：144.07 MB
- `app/dist` 总体积：148.59 MB
- admissions 分片文件数：272
- rank_table 分片文件数：8
- 最大 admissions 分片：`山西_2023_理科_all__part2.json`，7.79 MB
- 最大 rank_table 分片：`江西_2025_历史类.json`，约 0.05 MB

## 加载策略

- 首页不加载 admissions 大分片
- `/score-lookup` 初始只加载 `index.json` 和 `coverage.json`
- admissions 和 rank_table 都按用户选择的数据集按需加载
- 结果区默认只展示前 50 条，避免一次性渲染过多记录

## 当前判断

- 总体积仍偏大，但主要压力在前端候选数据文件，不在页面代码
- 单个 admissions 分片仍控制在 8 MB 以内
- 当前体积还可以部署到 GitHub Pages，但后续如果继续扩覆盖，应继续优先补质量，不要继续无上限扩文件量
