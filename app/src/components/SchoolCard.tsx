import { Link } from "react-router-dom";
import type { School } from "../types";
import { formatCategory } from "../utils/text";

interface SchoolCardProps {
  school: School;
  collected: boolean;
  onCollect: (school: School) => void;
}

function badgeClass(tag: string) {
  if (tag === "985") return "bg-amber-100 text-amber-800";
  if (tag === "211") return "bg-blue-100 text-blue-800";
  if (tag === "双一流") return "bg-emerald-100 text-emerald-800";
  return "bg-slate-100 text-slate-700";
}

export function SchoolCard({ school, collected, onCollect }: SchoolCardProps) {
  return (
    <article className="rounded-3xl bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Link to={`/schools/${school.school_id}`} className="text-lg font-semibold text-slate-900 hover:text-brand-700">
            {school.school_name}
          </Link>
          <p className="mt-1 text-sm text-slate-500">
            {school.province} · {school.city}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onCollect(school)}
          className={`rounded-full px-3 py-1.5 text-xs font-medium ${
            collected ? "bg-emerald-100 text-emerald-700" : "bg-brand-50 text-brand-700"
          }`}
        >
          {collected ? "已收藏" : "收藏"}
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-600">
        <div>
          <p className="text-xs text-slate-400">主管部门</p>
          <p>{school.department || "暂无数据"}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">院校层次</p>
          <p>{school.school_level || "暂无数据"}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">办学性质</p>
          <p>{school.ownership || "暂无数据"}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400">院校类型</p>
          <p>{formatCategory(school.school_type)}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(school.tags ?? []).map((tag) => (
          <span key={tag} className={`rounded-full px-3 py-1 text-xs font-medium ${badgeClass(tag)}`}>
            {tag}
          </span>
        ))}
      </div>

      <Link
        to={`/schools/${school.school_id}`}
        className="mt-5 inline-flex rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white"
      >
        查看详情
      </Link>
    </article>
  );
}
