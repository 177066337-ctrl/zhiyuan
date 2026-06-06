import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import {
  ScoreLookupForm,
  type ScoreLookupQualityFilter,
} from "../components/ScoreLookupForm";
import { ScoreLookupNotice } from "../components/ScoreLookupNotice";
import { ScoreLookupResultCard } from "../components/ScoreLookupResultCard";
import type {
  ScoreLookupAdmissionRecord,
  ScoreLookupCoverage,
  ScoreLookupDataset,
  ScoreLookupRankRecord,
  ScoreLookupResultItem,
  ScoreLookupResultSection,
} from "../types/scoreLookup";
import {
  buildScoreLookupResults,
  isUndergraduateBatch,
  loadScoreLookupAdmissions,
  loadScoreLookupCoverage,
  loadScoreLookupIndex,
  loadScoreLookupRankTable,
  qualitySortValue,
  resolveRankFromScore,
} from "../utils/scoreLookup";

const PAGE_SIZE = 50;
const SECTION_ORDER: ScoreLookupResultSection[] = [
  "位次参考结果",
  "仅分数参考结果",
  "数据异常或低置信度结果",
];

function groupResults(items: ScoreLookupResultItem[]) {
  const grouped = new Map<ScoreLookupResultSection, ScoreLookupResultItem[]>();
  for (const section of SECTION_ORDER) {
    grouped.set(section, []);
  }
  for (const item of items) {
    grouped.get(item.section)?.push(item);
  }
  return grouped;
}

function datasetMatchesQualityFilter(
  dataset: ScoreLookupDataset,
  filter: ScoreLookupQualityFilter,
) {
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

function datasetNotice(dataset: ScoreLookupDataset | null) {
  if (!dataset) {
    return "请先选择省份、年份、科类和批次。页面只会在你选定数据集后加载对应分片。";
  }
  if (dataset.quality_status === "warning") {
    return "当前数据集在抽检中发现异常，开放仅用于资料查看，不建议作为填报依据。";
  }
  if (dataset.quality_status === "candidate") {
    return "当前数据集尚未人工复核，可能存在字段错位、位次缺失、批次识别错误等问题，请谨慎参考。";
  }
  if (dataset.quality_status === "score_only") {
    return "当前数据集仅支持历史最低分参考，不支持可靠的分数换位次。";
  }
  return "该数据集已通过初步抽检，但仍不构成录取承诺。";
}

export function ScoreLookupPage() {
  const [index, setIndex] = useState<Awaited<ReturnType<typeof loadScoreLookupIndex>> | null>(
    null,
  );
  const [coverage, setCoverage] = useState<ScoreLookupCoverage | null>(null);
  const [indexLoading, setIndexLoading] = useState(true);
  const [indexError, setIndexError] = useState<string | null>(null);

  const [province, setProvince] = useState("");
  const [year, setYear] = useState("");
  const [subjectType, setSubjectType] = useState("");
  const [batch, setBatch] = useState("");
  const [score, setScore] = useState("");
  const [rank, setRank] = useState("");
  const [onlyUndergraduate, setOnlyUndergraduate] = useState(false);
  const [excludeLowConfidence, setExcludeLowConfidence] = useState(true);
  const [schoolKeyword, setSchoolKeyword] = useState("");
  const [minScoreFrom, setMinScoreFrom] = useState("");
  const [minScoreTo, setMinScoreTo] = useState("");
  const [qualityFilter, setQualityFilter] =
    useState<ScoreLookupQualityFilter>("all");

  const [datasetLoading, setDatasetLoading] = useState(false);
  const [datasetError, setDatasetError] = useState<string | null>(null);
  const [admissions, setAdmissions] = useState<ScoreLookupAdmissionRecord[]>([]);
  const [rankTable, setRankTable] = useState<ScoreLookupRankRecord[]>([]);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  useEffect(() => {
    let active = true;
    setIndexLoading(true);

    Promise.all([loadScoreLookupIndex(), loadScoreLookupCoverage()])
      .then(([indexPayload, coveragePayload]) => {
        if (!active) {
          return;
        }
        setIndex(indexPayload);
        setCoverage(coveragePayload);
        setIndexError(null);
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }
        setIndexError(error.message);
      })
      .finally(() => {
        if (active) {
          setIndexLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const datasets = useMemo(
    () =>
      (index?.datasets ?? [])
        .filter((item) => item.is_public)
        .sort((left, right) => {
          const byQuality =
            qualitySortValue(left.quality_status) - qualitySortValue(right.quality_status);
          if (byQuality !== 0) {
            return byQuality;
          }
          return (
            left.province.localeCompare(right.province, "zh-Hans-CN") ||
            left.year - right.year ||
            left.subject_type.localeCompare(right.subject_type, "zh-Hans-CN") ||
            left.batch.localeCompare(right.batch, "zh-Hans-CN")
          );
        }),
    [index],
  );

  const visibleDatasets = useMemo(
    () => datasets.filter((item) => datasetMatchesQualityFilter(item, qualityFilter)),
    [datasets, qualityFilter],
  );

  const selectedDataset = useMemo(
    () =>
      visibleDatasets.find(
        (item) =>
          item.province === province &&
          String(item.year) === year &&
          item.subject_type === subjectType &&
          item.batch === batch,
      ) ?? null,
    [batch, province, subjectType, visibleDatasets, year],
  );

  const selectedCoverage = useMemo(
    () =>
      coverage?.rows.find(
        (item) =>
          item.province === province &&
          String(item.year) === year &&
          item.subject_type === subjectType,
      ) ?? null,
    [coverage, province, subjectType, year],
  );

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [
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
  ]);

  useEffect(() => {
    if (!selectedDataset) {
      setAdmissions([]);
      setRankTable([]);
      setDatasetError(null);
      return;
    }

    let active = true;
    setDatasetLoading(true);
    setDatasetError(null);

    Promise.all([
      loadScoreLookupAdmissions(selectedDataset.admissions_file),
      loadScoreLookupRankTable(selectedDataset.rank_table_file),
    ])
      .then(([admissionsPayload, rankPayload]) => {
        if (!active) {
          return;
        }
        setAdmissions(admissionsPayload);
        setRankTable(rankPayload);
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }
        setDatasetError(error.message);
      })
      .finally(() => {
        if (active) {
          setDatasetLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedDataset]);

  const scoreNumber = score ? Number(score) : null;
  const rankNumber = rank ? Number(rank) : null;
  const resolvedRank = useMemo(
    () => (rankNumber ? rankNumber : resolveRankFromScore(rankTable, scoreNumber)),
    [rankNumber, rankTable, scoreNumber],
  );

  const results = useMemo(() => {
    if (!selectedDataset) {
      return [] as ScoreLookupResultItem[];
    }

    return buildScoreLookupResults(selectedDataset, admissions, resolvedRank)
      .filter((item) => !excludeLowConfidence || item.confidence !== "low")
      .filter((item) => !onlyUndergraduate || isUndergraduateBatch(item.batch))
      .filter((item) =>
        schoolKeyword
          ? item.school_name.toLowerCase().includes(schoolKeyword.trim().toLowerCase())
          : true,
      )
      .filter((item) =>
        minScoreFrom ? (item.min_score ?? -1) >= Number(minScoreFrom) : true,
      )
      .filter((item) =>
        minScoreTo ? (item.min_score ?? 9999) <= Number(minScoreTo) : true,
      );
  }, [
    admissions,
    excludeLowConfidence,
    minScoreFrom,
    minScoreTo,
    onlyUndergraduate,
    resolvedRank,
    schoolKeyword,
    selectedDataset,
  ]);

  const visibleResults = useMemo(
    () => results.slice(0, visibleCount),
    [results, visibleCount],
  );

  const groupedResults = useMemo(() => groupResults(results), [results]);
  const visibleGroupedResults = useMemo(
    () => groupResults(visibleResults),
    [visibleResults],
  );

  if (indexLoading) {
    return <LoadingState />;
  }

  if (indexError || !index) {
    return (
      <EmptyState
        title="分数查询索引加载失败"
        description={indexError ?? "请稍后重试。"}
      />
    );
  }

  const resultSummary = selectedDataset
    ? `当前已筛选出 ${results.length} 条历史参考记录`
    : `当前可选全国候选数据集 ${visibleDatasets.length} 个`;

  return (
    <div className="space-y-6">
      <ScoreLookupNotice
        title="按分数查志愿（全国候选试验版）"
        description="本页面为全国候选数据试验版，基于已整理的历史录取数据和一分一段数据进行查询。部分数据尚未人工复核，结果仅供资料查看和历史参考，不构成录取承诺。请以各省教育考试院、高校招生章程和当年招生计划为准。"
      />

      <ScoreLookupForm
        datasets={datasets}
        province={province}
        year={year}
        subjectType={subjectType}
        batch={batch}
        score={score}
        rank={rank}
        onlyUndergraduate={onlyUndergraduate}
        excludeLowConfidence={excludeLowConfidence}
        schoolKeyword={schoolKeyword}
        minScoreFrom={minScoreFrom}
        minScoreTo={minScoreTo}
        qualityFilter={qualityFilter}
        onProvinceChange={setProvince}
        onYearChange={setYear}
        onSubjectTypeChange={setSubjectType}
        onBatchChange={setBatch}
        onScoreChange={setScore}
        onRankChange={setRank}
        onOnlyUndergraduateChange={setOnlyUndergraduate}
        onExcludeLowConfidenceChange={setExcludeLowConfidence}
        onSchoolKeywordChange={setSchoolKeyword}
        onMinScoreFromChange={setMinScoreFrom}
        onMinScoreToChange={setMinScoreTo}
        onQualityFilterChange={setQualityFilter}
        onReset={() => {
          setProvince("");
          setYear("");
          setSubjectType("");
          setBatch("");
          setScore("");
          setRank("");
          setOnlyUndergraduate(false);
          setExcludeLowConfidence(true);
          setSchoolKeyword("");
          setMinScoreFrom("");
          setMinScoreTo("");
          setQualityFilter("all");
        }}
      />

      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">结果概览</h2>
            <p className="mt-1 text-sm text-slate-500">{resultSummary}</p>
            {selectedDataset ? (
              <p className="mt-1 text-xs text-slate-500">
                当前数据集：{selectedDataset.province} / {selectedDataset.year} /{" "}
                {selectedDataset.subject_type} / {selectedDataset.batch} /{" "}
                {selectedDataset.quality_label}
              </p>
            ) : null}
            {selectedCoverage ? (
              <p className="mt-1 text-xs text-slate-500">
                覆盖状态：{selectedCoverage.notice}
              </p>
            ) : null}
          </div>
          <div className="text-sm text-slate-600">
            <p>输入分数：{score || "未填写"}</p>
            <p>换算位次：{resolvedRank ?? "暂无"}</p>
          </div>
        </div>
      </section>

      <ScoreLookupNotice
        title="数据集状态提示"
        tone={selectedDataset?.quality_status === "warning" ? "warning" : "info"}
        description={datasetNotice(selectedDataset)}
      />

      {selectedDataset ? (
        <ScoreLookupNotice
          title="结果说明"
          tone="info"
          description="冲、稳、保分组只是历史数据对比结果，不代表实际录取结果。若没有可靠 rank table 或最低位次缺失，记录会自动降级到“仅分数参考结果”。"
        />
      ) : null}

      {datasetLoading ? <LoadingState /> : null}
      {datasetError ? (
        <EmptyState title="数据分片加载失败" description={datasetError} />
      ) : null}
      {!datasetLoading && !datasetError && selectedDataset && !results.length ? (
        <EmptyState
          title="暂无匹配结果"
          description="可以调整分数、位次、学校名称搜索或最低分区间后再试。"
        />
      ) : null}

      {!datasetLoading && !datasetError && results.length ? (
        <div className="space-y-6">
          {SECTION_ORDER.map((section) => {
            const groupItems = groupedResults.get(section) ?? [];
            const visibleItems = visibleGroupedResults.get(section) ?? [];
            if (!groupItems.length) {
              return null;
            }
            return (
              <section key={section} className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{section}</h3>
                  <p className="text-sm text-slate-500">共 {groupItems.length} 条</p>
                </div>
                <div className="grid gap-4">
                  {visibleItems.map((item) => (
                    <ScoreLookupResultCard
                      key={[
                        item.school_code,
                        item.school_name,
                        item.major_group_code,
                        item.major_name,
                        item.min_score,
                        item.min_rank,
                      ].join("_")}
                      item={item}
                    />
                  ))}
                </div>
              </section>
            );
          })}

          {visibleCount < results.length ? (
            <div className="text-center">
              <button
                type="button"
                onClick={() => setVisibleCount((value) => value + PAGE_SIZE)}
                className="rounded-full bg-brand-600 px-5 py-3 text-sm font-medium text-white"
              >
                加载更多
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
