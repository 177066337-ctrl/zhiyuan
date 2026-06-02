import { useNavigate, useParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { useSchools } from "../hooks/useSchools";
import { useWishlist } from "../hooks/useWishlist";
import { fallbackText, formatCategory } from "../utils/text";

export function SchoolDetailPage() {
  const { schoolId } = useParams();
  const { data, loading, error } = useSchools();
  const wishlist = useWishlist();
  const navigate = useNavigate();

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <EmptyState title="院校详情加载失败" description={error} />;
  }

  const school = data.find((item) => item.school_id === schoolId);

  if (!school) {
    return <EmptyState title="未找到该院校" description="请返回院校列表重新选择。" />;
  }

  const fields = [
    ["省份", school.province],
    ["城市", school.city],
    ["主管部门", school.department],
    ["院校层次", school.school_level],
    ["办学性质", school.ownership],
    ["院校类型", formatCategory(school.school_type)],
    ["数据来源", school.source_file],
    ["来源行", String(school.source_row)],
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{school.school_name}</h1>
            <p className="mt-2 text-sm text-slate-500">{school.province} · {school.city}</p>
          </div>
          <button
            type="button"
            onClick={() => wishlist.addSchool(school)}
            className={`rounded-full px-4 py-2 text-sm font-medium ${
              wishlist.isCollected(school.school_id)
                ? "bg-emerald-100 text-emerald-700"
                : "bg-brand-600 text-white"
            }`}
          >
            {wishlist.isCollected(school.school_id) ? "已收藏" : "收藏院校"}
          </button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {fields.map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs text-slate-400">{label}</p>
              <p className="mt-2 text-sm text-slate-700">{value || "暂无数据"}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 space-y-4">
          <div className="rounded-2xl bg-blue-50 p-4 text-sm leading-6 text-slate-700">
            院校类型为辅助筛选分类，当前主要基于院校名称关键词做弱规则归类，不等同于官方正式分类。
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-900">核心标签</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {(school.tags ?? []).length > 0 ? (
                school.tags?.map((tag) => (
                  <span key={tag} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {tag}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">暂无数据</span>
              )}
            </div>
          </div>

          {school.double_first_class_disciplines?.length ? (
            <div>
              <p className="text-sm font-semibold text-slate-900">双一流建设学科</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {school.double_first_class_disciplines.map((discipline) => (
                  <span key={discipline} className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                    {discipline}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          <div>
            <p className="text-sm font-semibold text-slate-900">标签来源</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
              {(school.tag_sources ?? []).length > 0 ? (
                school.tag_sources?.map((source) => <li key={source}>{source}</li>)
              ) : (
                <li>暂无数据</li>
              )}
            </ul>
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-900">双一流建设学科（文本）</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {fallbackText(
                school.double_first_class_disciplines?.join("、"),
                "暂无数据",
              )}
            </p>
          </div>
        </div>
      </section>

      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
      >
        返回上一页
      </button>
    </div>
  );
}
