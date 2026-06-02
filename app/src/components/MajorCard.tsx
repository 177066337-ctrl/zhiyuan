import { Link } from "react-router-dom";
import type { Major } from "../types";
import { fallbackText } from "../utils/text";

interface MajorCardProps {
  major: Major;
  collected: boolean;
  onCollect: (major: Major) => void;
}

export function MajorCard({ major, collected, onCollect }: MajorCardProps) {
  return (
    <article className="rounded-3xl bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Link to={`/majors/${major.major_id}`} className="text-lg font-semibold text-slate-900 hover:text-brand-700">
            {major.major_name}
          </Link>
          <p className="mt-1 text-sm text-slate-500">{major.major_code}</p>
        </div>
        <button
          type="button"
          onClick={() => onCollect(major)}
          className={`rounded-full px-3 py-1.5 text-xs font-medium ${
            collected ? "bg-emerald-100 text-emerald-700" : "bg-brand-50 text-brand-700"
          }`}
        >
          {collected ? "已收藏" : "收藏"}
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-600">
        <div>
          <p className="text-xs text-slate-400">培养层次</p>
          <p>{major.degree_level || "暂无数据"}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">门类 / 大类</p>
          <p>{fallbackText(major.major_discipline)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">专业类</p>
          <p>{fallbackText(major.major_category)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">授予学位</p>
          <p>{major.degree || "暂无数据"}</p>
        </div>
      </div>

      <Link
        to={`/majors/${major.major_id}`}
        className="mt-5 inline-flex rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white"
      >
        查看详情
      </Link>
    </article>
  );
}
