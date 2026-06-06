import type {
  ScoreLookupAdmissionRecord,
  ScoreLookupAdmissionsManifest,
  ScoreLookupCoverage,
  ScoreLookupDataset,
  ScoreLookupIndex,
  ScoreLookupQualityStatus,
  ScoreLookupRankRecord,
  ScoreLookupResultItem,
  ScoreLookupResultSection,
  ScoreLookupStrategyLabel,
} from "../types/scoreLookup";

function dataUrl(path: string) {
  return `${import.meta.env.BASE_URL}${path}`;
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(dataUrl(path), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`无法加载数据文件：${path}`);
  }
  return (await response.json()) as T;
}

export async function loadScoreLookupIndex() {
  return fetchJson<ScoreLookupIndex>("data/score-lookup/index.json");
}

export async function loadScoreLookupCoverage() {
  return fetchJson<ScoreLookupCoverage>("data/score-lookup/coverage.json");
}

export async function loadScoreLookupAdmissions(
  file: string,
): Promise<ScoreLookupAdmissionRecord[]> {
  const payload = await fetchJson<
    ScoreLookupAdmissionRecord[] | ScoreLookupAdmissionsManifest
  >(file);
  if (Array.isArray(payload)) {
    return payload;
  }

  const shards = await Promise.all(
    payload.shards.map((shard) => fetchJson<ScoreLookupAdmissionRecord[]>(shard)),
  );
  return shards.flat();
}

export async function loadScoreLookupRankTable(file: string) {
  if (!file) {
    return [] as ScoreLookupRankRecord[];
  }
  return fetchJson<ScoreLookupRankRecord[]>(file);
}

export function resolveRankFromScore(
  records: ScoreLookupRankRecord[],
  score: number | null,
): number | null {
  if (score === null || Number.isNaN(score) || !records.length) {
    return null;
  }

  const exact = records.find((item) => item.score === score);
  if (exact) {
    return exact.rank;
  }

  const fallback = records.find((item) => item.score <= score);
  const last = records.length ? records[records.length - 1] : null;
  return fallback?.rank ?? last?.rank ?? null;
}

export function isUndergraduateBatch(batch: string) {
  return batch.includes("本科");
}

export function formatDatasetLabel(dataset: ScoreLookupDataset) {
  return `${dataset.province} / ${dataset.year} / ${dataset.subject_type} / ${dataset.batch}`;
}

export function qualitySortValue(status: ScoreLookupQualityStatus) {
  switch (status) {
    case "verified":
      return 0;
    case "candidate":
      return 1;
    case "warning":
      return 2;
    case "score_only":
      return 3;
    default:
      return 4;
  }
}

export function qualityBadgeClass(status: ScoreLookupQualityStatus) {
  switch (status) {
    case "verified":
      return "bg-emerald-100 text-emerald-700";
    case "candidate":
      return "bg-sky-100 text-sky-700";
    case "warning":
      return "bg-amber-100 text-amber-800";
    case "score_only":
      return "bg-slate-100 text-slate-700";
    default:
      return "bg-rose-100 text-rose-700";
  }
}

function strategyLabel(userRank: number | null, minRank: number | null) {
  if (userRank === null || minRank === null) {
    return "仅分数参考" as ScoreLookupStrategyLabel;
  }
  if (userRank >= minRank * 0.95 && userRank <= minRank * 1.1) {
    return "可冲一冲" as ScoreLookupStrategyLabel;
  }
  if (userRank < minRank * 0.95 && userRank >= minRank * 0.75) {
    return "较为匹配" as ScoreLookupStrategyLabel;
  }
  if (userRank < minRank * 0.75) {
    return "相对保守" as ScoreLookupStrategyLabel;
  }
  return "仅分数参考" as ScoreLookupStrategyLabel;
}

function resultSection(
  dataset: ScoreLookupDataset,
  record: ScoreLookupAdmissionRecord,
  userRank: number | null,
) {
  if (
    dataset.quality_status === "warning" ||
    dataset.quality_status === "unavailable" ||
    record.confidence === "low"
  ) {
    return "数据异常或低置信度结果" as ScoreLookupResultSection;
  }

  if (
    userRank !== null &&
    dataset.quality_status !== "score_only" &&
    record.min_rank !== null
  ) {
    return "位次参考结果" as ScoreLookupResultSection;
  }

  return "仅分数参考结果" as ScoreLookupResultSection;
}

function buildRiskNotice(dataset: ScoreLookupDataset, record: ScoreLookupAdmissionRecord) {
  if (dataset.quality_status === "warning") {
    return "抽检发现问题，开放仅用于资料查看，不建议直接作为填报依据。";
  }
  if (dataset.quality_status === "candidate") {
    return "当前数据集尚未人工复核，仅供历史数据参考。";
  }
  if (dataset.quality_status === "score_only") {
    return "当前数据集缺少可靠位次支撑，只能做历史最低分参考。";
  }
  if (record.confidence === "low") {
    return "该记录置信度较低，请结合原始来源谨慎查看。";
  }
  return "该数据集已通过初步抽检，但仍不构成录取承诺。";
}

export function buildScoreLookupResults(
  dataset: ScoreLookupDataset,
  admissions: ScoreLookupAdmissionRecord[],
  userRank: number | null,
) {
  const rows: ScoreLookupResultItem[] = admissions.map((record) => {
    const minRank = record.min_rank;
    const rankDiff =
      userRank !== null && minRank !== null ? minRank - userRank : null;
    return {
      ...record,
      datasetYear: dataset.year,
      userRank,
      rankDiff,
      strategyLabel: strategyLabel(userRank, minRank),
      section: resultSection(dataset, record, userRank),
      qualityStatus: dataset.quality_status,
      qualityLabel: dataset.quality_label,
      qualityNotice: dataset.quality_notice,
      riskNotice: buildRiskNotice(dataset, record),
      hasRankReference:
        userRank !== null &&
        dataset.quality_status !== "score_only" &&
        record.min_rank !== null,
    };
  });

  return rows.sort((left, right) => {
    if (left.section !== right.section) {
      const order: ScoreLookupResultSection[] = [
        "位次参考结果",
        "仅分数参考结果",
        "数据异常或低置信度结果",
      ];
      return order.indexOf(left.section) - order.indexOf(right.section);
    }
    if (left.rankDiff === null && right.rankDiff === null) {
      return (right.min_score ?? 0) - (left.min_score ?? 0);
    }
    if (left.rankDiff === null) {
      return 1;
    }
    if (right.rankDiff === null) {
      return -1;
    }
    return left.rankDiff - right.rankDiff;
  });
}
