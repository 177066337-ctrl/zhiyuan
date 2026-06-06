export type ScoreLookupQualityStatus =
  | "verified"
  | "candidate"
  | "warning"
  | "score_only"
  | "unavailable";

export type ScoreLookupResultSection =
  | "位次参考结果"
  | "仅分数参考结果"
  | "数据异常或低置信度结果";

export type ScoreLookupStrategyLabel =
  | "可冲一冲"
  | "较为匹配"
  | "相对保守"
  | "仅分数参考";

export interface ScoreLookupDataset {
  dataset_id: string;
  province: string;
  year: number;
  subject_type: string;
  batch: string;
  admissions_file: string;
  rank_table_file: string;
  admissions_records: number;
  rank_table_records: number;
  min_score_complete_rate: number;
  min_rank_complete_rate: number;
  score_complete_rate: number;
  rank_complete_rate: number;
  quality_grade: "A" | "B" | "C";
  enabled: boolean;
  notes: string;
  quality_status: ScoreLookupQualityStatus;
  quality_label: string;
  quality_notice: string;
  is_public: boolean;
  requires_warning: boolean;
}

export interface ScoreLookupIndex {
  generated_at: string;
  version: string;
  notice: string;
  datasets: ScoreLookupDataset[];
}

export interface ScoreLookupCoverageRow {
  province: string;
  year: number;
  subject_type: string;
  status:
    | "open_verified"
    | "open_candidate"
    | "open_warning"
    | "score_only"
    | "reviewing"
    | "preparing"
    | "unavailable";
  label: string;
  notice: string;
  batches: string[];
  public_batches: string[];
}

export interface ScoreLookupCoverage {
  generated_at: string;
  notice: string;
  rows: ScoreLookupCoverageRow[];
}

export interface ScoreLookupAdmissionRecord {
  school_code: string;
  school_name: string;
  major_group_code: string;
  major_group_name: string;
  major_code: string;
  major_name: string;
  min_score: number | null;
  min_rank: number | null;
  batch: string;
  remarks: string;
  source_file: string;
  confidence: string;
}

export interface ScoreLookupRankRecord {
  score: number;
  rank: number;
  same_score_count: number | null;
  cumulative_count: number | null;
}

export interface ScoreLookupAdmissionsManifest {
  dataset_id: string;
  shards: string[];
  total_records: number;
}

export interface ScoreLookupResultItem extends ScoreLookupAdmissionRecord {
  datasetYear: number;
  userRank: number | null;
  rankDiff: number | null;
  section: ScoreLookupResultSection;
  strategyLabel: ScoreLookupStrategyLabel;
  qualityStatus: ScoreLookupQualityStatus;
  qualityLabel: string;
  qualityNotice: string;
  riskNotice: string;
  hasRankReference: boolean;
}
