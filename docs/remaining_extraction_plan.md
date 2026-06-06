# Remaining Extraction Plan

- 剩余任务总数: 484
- 只处理尚未完成或未纳入一期自动抽取范围的任务。
- 已存在且 JSON 可解析的输出默认跳过。
- OCR 任务本阶段只做样本探测，不做全量识别。
- low 优先级 admissions / rank_table 进入独立 remaining 输出目录，不回写 national_*。
- 每个任务记录状态并定期写进度报告。