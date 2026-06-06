import type { ScoreLookupResultItem } from "../types/scoreLookup";
import { qualityBadgeClass } from "../utils/scoreLookup";

interface ScoreLookupResultCardProps {
  item: ScoreLookupResultItem;
}

function confidenceTone(confidence: string) {
  if (confidence === "high") {
    return "bg-emerald-100 text-emerald-700";
  }
  if (confidence === "medium") {
    return "bg-sky-100 text-sky-700";
  }
  return "bg-slate-100 text-slate-700";
}

export function ScoreLookupResultCard({ item }: ScoreLookupResultCardProps) {
  const title = item.major_group_name || item.major_name || "未细分到专业组";

  return (
    <article className="rounded-3xl bg-white p-5 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{item.school_name}</h3>
          <p className="mt-1 text-sm text-slate-600">{title}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            {item.strategyLabel}
          </span>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${qualityBadgeClass(
              item.qualityStatus,
            )}`}
          >
            {item.qualityLabel}
          </span>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${confidenceTone(
              item.confidence,
            )}`}
          >
            {item.confidence || "low"}
          </span>
        </div>
      </div>

      <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
        <div>
          <p className="text-xs text-slate-400">批次</p>
          <p className="mt-1 font-medium text-slate-900">{item.batch || "未标注"}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">历史最低分</p>
          <p className="mt-1 font-medium text-slate-900">
            {item.min_score ?? "当前字段尚未结构化，后续版本补充。"}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">历史最低位次</p>
          <p className="mt-1 font-medium text-slate-900">
            {item.min_rank ?? "当前字段尚未结构化，后续版本补充。"}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">与用户位次差</p>
          <p className="mt-1 font-medium text-slate-900">
            {item.rankDiff === null ? "仅分数参考" : item.rankDiff}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-600">
        <p className="font-medium text-slate-900">{item.qualityNotice}</p>
        <p className="mt-1 text-xs leading-5 text-slate-500">{item.riskNotice}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-500">
        <span>数据年份：{item.datasetYear}</span>
        <span>数据来源：{item.source_file || "未标注"}</span>
      </div>
    </article>
  );
}
