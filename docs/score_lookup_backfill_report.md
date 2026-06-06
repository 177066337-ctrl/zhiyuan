# Score Lookup Backfill Report

## 本次回填概况

- 补全前开放数据集：88 个
- 补全后开放数据集：88 个
- 补全前质量分布：`verified 2 / warning 3 / candidate 3 / score_only 80`
- 补全后质量分布：`verified 2 / warning 3 / candidate 7 / score_only 76`

## 回填执行结果

- `rank_table` 回填任务：13 个
  - 新生成 normalized 文件：9 个
  - 其中可直接放行：0 个
  - `needs_manual_review`：9 个
  - 同一省份/年份/科类重复命中而跳过：4 个
- `admissions` 回填任务：8 个
  - 新生成 normalized 文件：8 个
  - `completed`：5 个
  - `needs_manual_review`：3 个

## 升级效果

- 从 `score_only` 升级为 `candidate`：4 个数据集
  - 内蒙古 2024 文科 本科一批
  - 内蒙古 2024 文科 本科二批
  - 内蒙古 2024 理科 本科一批
  - 内蒙古 2024 理科 本科二批
- 另外保留的 `candidate`：
  - 福建 2023 物理类 本科批
  - 福建 2023 物理类 专科批
  - 广东 2025 体育类 本科批

## 仍然无法补全的核心原因

- 大量数据集仍缺可直接放行的 `rank_table`
- 一部分缺口虽然找到候选文件，但抽取后排序或完整度不足，只能进入人工复核
- `needs_ocr` 的高价值缺口仍然存在，本阶段只做探测，没有全量 OCR

## 需要 OCR 的缺口

- 河北 2024 理科：本科批、专科批、本科提前批、专科提前批
- 云南 2024 文科/理科：本科一批、本科二批、高职专科批
- 江苏 2022-2023 历史类/物理类：本科批、专科批
- 陕西 2026 物理类 本科批 admissions
- 江西 2025 体育类、艺术类 征集志愿 admissions

## 需要人工复核的缺口

- 安徽 2025 理科 admissions 多个批次
- 广西 2025 理科 本科提前批 admissions
- 江苏 2020 理科 rank_table
- 江西 2024 历史类 rank_table
- 河北 2024 理科 rank_table
- 甘肃 2024 历史类/物理类 rank_table
- 重庆 2024 历史类/物理类 rank_table

## 下一步建议

1. 如果继续补覆盖，优先做 `rank_table` 的定点 OCR 和人工复核。
2. 不建议为了追求省份数量继续扩前端 admissions，而忽视 `rank_table` 缺口。
3. 当前已经可以部署，但应继续保持“全国候选试验版”的风险定位。
