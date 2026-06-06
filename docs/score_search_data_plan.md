# 按分数查询志愿数据方案

## 1. 目前是否具备“按分数查询志愿”的最低数据条件？

- 部分具备，但还不具备全国统一上线条件。
- 如果按“单省 + 单科类 + 单年份”试点，现有资料已经足够进入数据抽取验证阶段。

## 2. 如果不具备，还缺哪些字段？

- 同一省份下稳定统一的院校代码、院校专业组代码、专业代码映射。
- 与录取数据同口径的一分一段表或位次表。
- 对应年份招生计划数。
- 选科要求与专业组之间的结构化映射。

## 3. 最小可用版本应该先支持哪个省、哪个科类？

- 建议先做 `山西 2025 物理类` 或 `山西 2025 历史类`。
- 备选是 `山东 2025 夏季高考文化成绩`，但山东志愿规则和数据口径更特殊，适合作为第二试点。

## 4. admissions.json 建议字段结构

```json
{
  "province": "",
  "year": 2025,
  "subject_type": "物理类",
  "batch": "本科",
  "school_name": "",
  "school_code": "",
  "major_group_name": "",
  "major_group_code": "",
  "major_name": "",
  "major_code": "",
  "min_score": 0,
  "min_rank": 0,
  "avg_score": null,
  "max_score": null,
  "plan_count": null,
  "source_file": "",
  "source_page": null,
  "source_row": null
}
```

## 5. rank_tables.json 建议字段结构

```json
{
  "province": "",
  "year": 2025,
  "subject_type": "物理类",
  "score": 600,
  "same_score_count": 0,
  "cumulative_count": 0,
  "rank_min": 0,
  "rank_max": 0,
  "source_file": "",
  "source_row": null
}
```

## 6. plans.json 建议字段结构

```json
{
  "province": "",
  "year": 2026,
  "subject_type": "物理类",
  "batch": "",
  "school_name": "",
  "school_code": "",
  "major_group_name": "",
  "major_group_code": "",
  "major_name": "",
  "major_code": "",
  "plan_count": 0,
  "tuition": null,
  "duration": "",
  "source_file": "",
  "source_row": null
}
```

## 7. 前端“按分数查志愿”页面需要哪些输入项

- 省份
- 年份
- 科类（历史类 / 物理类 / 文科 / 理科 / 综合）
- 分数
- 可选：位次
- 可选：批次
- 可选：地区 / 院校标签 / 办学层次

## 8. 哪些结果可以展示，哪些不能展示

- 可以展示：历史最低分、历史最低位次、对应院校/专业组、招生计划、数据来源。
- 可以展示：按历史数据筛出的“可参考院校列表”。
- 不能展示：录取概率、稳录结论、保底承诺、拟录取判断。

## 9. 如何避免把参考结果包装成录取承诺

- 页面文案统一使用“历史数据参考”“辅助筛选”“仅供参考”。
- 不使用“能上”“稳上”“保录”等确定性措辞。
- 强制展示免责声明：请以当年省考试院、高校招生章程和招生计划为准。
