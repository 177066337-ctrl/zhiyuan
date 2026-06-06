# National Candidate Release Report

- 开放数据集总数：88 个
- `verified`：2 个
- `warning`：3 个
- `candidate`：7 个
- `score_only`：76 个
- `unavailable`：0 个前端公开项
- 省份覆盖：20 个
- 年份覆盖：9 个
- 科类覆盖：5 个
- 前端数据总体积：144.07 MB
- 最大单个 admissions 分片：`山西_2023_理科_all__part2.json`，7.79 MB

## 当前质量分层

- `verified`
  - 福建 2023 历史类 本科批
  - 福建 2023 历史类 专科批
- `warning`
  - 江西 2025 历史类 本科
  - 江西 2025 历史类 专科
  - 江西 2025 历史类 征集志愿
- `candidate`
  - 内蒙古 2024 文科 本科一批
  - 内蒙古 2024 文科 本科二批
  - 内蒙古 2024 理科 本科一批
  - 内蒙古 2024 理科 本科二批
  - 福建 2023 物理类 本科批
  - 福建 2023 物理类 专科批
  - 广东 2025 体育类 本科批

## 需要谨慎的数据

- 江西 2025 历史类：已开放，但抽检发现问题，仍应保持 `warning`
- 其他 `candidate`：尚未人工复核，只能作为历史参考
- `score_only`：仅支持历史最低分查询，不支持可靠的分数换位次

## 仍未开放的内容

- 16G 原始资料
- `data_work` 原始大 JSON 全集
- `needs_ocr` 原始文件
- `failed` 任务结果
- `plans_normalized` 全量文件
- `subject_requirements_normalized`

## 结论

- 本次补全后，前端发布层仍然是“全国候选试验版”
- 可公开范围扩大没有问题，但真正限制用户体验的仍然是 `rank_table` 覆盖不足
- 后续若要继续提升可用性，优先级应是：
  1. 补高质量 `rank_table`
  2. 复核 `warning` 和 `candidate`
  3. 再考虑扩大更多科类或批次
