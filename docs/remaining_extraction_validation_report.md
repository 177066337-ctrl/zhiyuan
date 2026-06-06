# Remaining Extraction Validation Report

- remaining admissions 文件数: 148
- remaining admissions 记录数: 1082063
- remaining rank_table 文件数: 5
- remaining rank_table 记录数: 0
- plans 文件数: 244
- plans 记录数: 6477762
- subject_requirement 文件数: 5
- subject_requirement 记录数: 0
- OCR probe 文件数: 68
- JSON 解析错误数量: 0
- 低置信度比例 admissions: 77.81%
- 低置信度比例 rank_table: 0.00%
- 低置信度比例 plans: 74.18%
- 低置信度比例 subject_requirement: 0.00%
- failed 数量: 2
- timeout 数量: 0
- needs_manual_review 数量: 56

## 按 document_type 统计
- admissions: 180
- plans: 248
- rank_table: 51
- subject_requirement: 5

## Failed / Timeout Tasks
- plans_浙江_2022_未知_all_xlsx: failed - Traceback (most recent call last):
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 175, in <module>
    main()
    ~~~~^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 128, in main
    raise SystemExit(run_single_task(sys.argv[2]))
                     ~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 119, in run_single_task
    raw_rows, records = parse_plan_task(task)
                        ~~~~~~~~~~~~~~~^^^^^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 80, in parse_plan_task
    rows_by_sheet = read_excel_rows(path)
  File "D:\2026\zhiyuan\scripts\national_extraction_common.py", line 409, in read_excel_rows
    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Python314\Lib\site-packages\openpyxl\worksheet\_read_only.py", line 85, in _cells_by_row
    for idx, row in parser.parse():
           
- plans_浙江_2022_未知_all_xlsx: failed - Traceback (most recent call last):
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 175, in <module>
    main()
    ~~~~^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 128, in main
    raise SystemExit(run_single_task(sys.argv[2]))
                     ~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 119, in run_single_task
    raw_rows, records = parse_plan_task(task)
                        ~~~~~~~~~~~~~~~^^^^^^
  File "D:\2026\zhiyuan\scripts\extract_plans_batch.py", line 80, in parse_plan_task
    rows_by_sheet = read_excel_rows(path)
  File "D:\2026\zhiyuan\scripts\national_extraction_common.py", line 409, in read_excel_rows
    for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Python314\Lib\site-packages\openpyxl\worksheet\_read_only.py", line 85, in _cells_by_row
    for idx, row in parser.parse():
           