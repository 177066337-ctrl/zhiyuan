import { useMemo, useState } from "react";
import type { ScoreLookupDataset } from "../types/scoreLookup";
import { qualityBadgeClass } from "../utils/scoreLookup";

export type ScoreLookupQualityFilter =
  | "all"
  | "verified"
  | "with_candidate"
  | "with_warning";

interface ScoreLookupFormProps {
  datasets: ScoreLookupDataset[];
  province: string;
  year: string;
  subjectType: string;
  batch: string;
  score: string;
  rank: string;
  onlyUndergraduate: boolean;
  excludeLowConfidence: boolean;
  schoolKeyword: string;
  minScoreFrom: string;
  minScoreTo: string;
  qualityFilter: ScoreLookupQualityFilter;
  onProvinceChange: (value: string) => void;
  onYearChange: (value: string) => void;
  onSubjectTypeChange: (value: string) => void;
  onBatchChange: (value: string) => void;
  onScoreChange: (value: string) => void;
  onRankChange: (value: string) => void;
  onOnlyUndergraduateChange: (value: boolean) => void;
  onExcludeLowConfidenceChange: (value: boolean) => void;
  onSchoolKeywordChange: (value: string) => void;
  onMinScoreFromChange: (value: string) => void;
  onMinScoreToChange: (value: string) => void;
  onQualityFilterChange: (value: ScoreLookupQualityFilter) => void;
  onReset: () => void;
}

function uniqueSorted(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((left, right) =>
    left.localeCompare(right, "zh-Hans-CN"),
  );
}

function qualityMatches(dataset: ScoreLookupDataset, filter: ScoreLookupQualityFilter) {
  switch (filter) {
    case "verified":
      return dataset.quality_status === "verified";
    case "with_candidate":
      return ["verified", "candidate", "score_only"].includes(dataset.quality_status);
    case "with_warning":
      return dataset.is_public;
    default:
      return dataset.is_public;
  }
}

export function ScoreLookupForm(props: ScoreLookupFormProps) {
  const {
    datasets,
    province,
    year,
    subjectType,
    batch,
    score,
    rank,
    onlyUndergraduate,
    excludeLowConfidence,
    schoolKeyword,
    minScoreFrom,
    minScoreTo,
    qualityFilter,
    onProvinceChange,
    onYearChange,
    onSubjectTypeChange,
    onBatchChange,
    onScoreChange,
    onRankChange,
    onOnlyUndergraduateChange,
    onExcludeLowConfidenceChange,
    onSchoolKeywordChange,
    onMinScoreFromChange,
    onMinScoreToChange,
    onQualityFilterChange,
    onReset,
  } = props;

  const [expanded, setExpanded] = useState(false);

  const filteredDatasets = useMemo(
    () => datasets.filter((item) => qualityMatches(item, qualityFilter)),
    [datasets, qualityFilter],
  );

  const provinceOptions = uniqueSorted(filteredDatasets.map((item) => item.province));
  const yearOptions = uniqueSorted(
    filteredDatasets
      .filter((item) => !province || item.province === province)
      .map((item) => String(item.year)),
  );
  const subjectOptions = uniqueSorted(
    filteredDatasets
      .filter(
        (item) =>
          (!province || item.province === province) &&
          (!year || String(item.year) === year),
      )
      .map((item) => item.subject_type),
  );
  const batchOptions =
    province && year && subjectType
      ? filteredDatasets
          .filter(
            (item) =>
              item.province === province &&
              String(item.year) === year &&
              item.subject_type === subjectType,
          )
          .sort((left, right) => left.batch.localeCompare(right.batch, "zh-Hans-CN"))
      : [];

  return (
    <section className="rounded-3xl bg-white p-4 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">查询条件</h2>
          <p className="text-sm text-slate-500">
            页面初始只加载候选索引。只有在选定省份、年份、科类和批次后，才会按需加载对应 admissions 和 rank table 分片。
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600 md:hidden"
          >
            {expanded ? "收起筛选" : "展开筛选"}
          </button>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600"
          >
            重置
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
          当前候选数据集：{filteredDatasets.length}
        </span>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">
          已抽检通过
        </span>
        <span className="rounded-full bg-sky-100 px-3 py-1 text-sky-700">
          未人工复核
        </span>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-800">
          抽检有问题
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-700">
          仅分数参考
        </span>
      </div>

      <div className={`mt-4 space-y-4 ${expanded ? "block" : "hidden md:block"}`}>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="flex flex-col gap-2 text-sm">
            <span>数据质量</span>
            <select
              value={qualityFilter}
              onChange={(event) =>
                onQualityFilterChange(event.target.value as ScoreLookupQualityFilter)
              }
              className="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <option value="all">全部公开候选</option>
              <option value="verified">只看已抽检通过</option>
              <option value="with_candidate">包含未复核候选数据</option>
              <option value="with_warning">包含警示数据</option>
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm">
            <span>省份</span>
            <select
              value={province}
              onChange={(event) => onProvinceChange(event.target.value)}
              className="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <option value="">请选择</option>
              {provinceOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm">
            <span>年份</span>
            <select
              value={year}
              onChange={(event) => onYearChange(event.target.value)}
              className="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <option value="">请选择</option>
              {yearOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm">
            <span>科类</span>
            <select
              value={subjectType}
              onChange={(event) => onSubjectTypeChange(event.target.value)}
              className="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <option value="">请选择</option>
              {subjectOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 text-sm">
            <span>批次</span>
            <select
              value={batch}
              onChange={(event) => onBatchChange(event.target.value)}
              className="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <option value="">请选择</option>
              {batchOptions.map((option) => (
                <option key={option.dataset_id} value={option.batch}>
                  {option.batch} · {option.quality_label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="flex flex-col gap-2 text-sm">
            <span>分数</span>
            <input
              value={score}
              onChange={(event) => onScoreChange(event.target.value)}
              inputMode="decimal"
              placeholder="例如 560"
              className="rounded-2xl border border-slate-200 px-4 py-3"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span>位次，可选</span>
            <input
              value={rank}
              onChange={(event) => onRankChange(event.target.value)}
              inputMode="numeric"
              placeholder="如果已知位次，优先使用位次"
              className="rounded-2xl border border-slate-200 px-4 py-3"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            <span>学校名称搜索</span>
            <input
              value={schoolKeyword}
              onChange={(event) => onSchoolKeywordChange(event.target.value)}
              placeholder="支持按学校名称筛选"
              className="rounded-2xl border border-slate-200 px-4 py-3"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-2 text-sm">
              <span>最低分下限</span>
              <input
                value={minScoreFrom}
                onChange={(event) => onMinScoreFromChange(event.target.value)}
                inputMode="decimal"
                className="rounded-2xl border border-slate-200 px-4 py-3"
              />
            </label>
            <label className="flex flex-col gap-2 text-sm">
              <span>最低分上限</span>
              <input
                value={minScoreTo}
                onChange={(event) => onMinScoreToChange(event.target.value)}
                inputMode="decimal"
                className="rounded-2xl border border-slate-200 px-4 py-3"
              />
            </label>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 text-sm text-slate-600">
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={onlyUndergraduate}
              onChange={(event) => onOnlyUndergraduateChange(event.target.checked)}
            />
            只看本科
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={excludeLowConfidence}
              onChange={(event) => onExcludeLowConfidenceChange(event.target.checked)}
            />
            排除低置信度记录
          </label>
        </div>

        {province && year && subjectType && batchOptions.length ? (
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-3 text-sm text-slate-600">
            <p className="font-medium text-slate-900">当前批次可选数据集</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {batchOptions.map((option) => (
                <span
                  key={option.dataset_id}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${qualityBadgeClass(
                    option.quality_status,
                  )}`}
                >
                  {option.batch} · {option.quality_label}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
