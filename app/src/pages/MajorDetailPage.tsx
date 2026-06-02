import { useNavigate, useParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { useMajors } from "../hooks/useMajors";
import { useWishlist } from "../hooks/useWishlist";
import { fallbackText } from "../utils/text";

export function MajorDetailPage() {
  const { majorId } = useParams();
  const { data, loading, error } = useMajors();
  const wishlist = useWishlist();
  const navigate = useNavigate();

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <EmptyState title="专业详情加载失败" description={error} />;
  }

  const major = data.find((item) => item.major_id === majorId);
  if (!major) {
    return <EmptyState title="未找到该专业" description="请返回专业列表重新选择。" />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">{major.major_name}</h1>
            <p className="mt-2 text-sm text-slate-500">{major.major_code} · {major.degree_level}</p>
          </div>
          <button
            type="button"
            onClick={() => wishlist.addMajor(major)}
            className={`rounded-full px-4 py-2 text-sm font-medium ${
              wishlist.isCollected(major.major_id)
                ? "bg-emerald-100 text-emerald-700"
                : "bg-brand-600 text-white"
            }`}
          >
            {wishlist.isCollected(major.major_id) ? "已收藏" : "收藏专业"}
          </button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {[
            ["门类 / 大类", major.major_discipline],
            ["专业类", major.major_category],
            ["授予学位", major.degree],
            ["修业年限", major.duration],
            [
              "选科要求",
              major.subject_requirement || "当前字段尚未结构化，后续版本补充。",
            ],
            [
              "专业简介",
              major.description || "当前字段尚未结构化，后续版本补充。",
            ],
            ["数据来源", major.source_file],
            ["来源行", String(major.source_row)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-slate-50 p-4">
              <p className="text-xs text-slate-400">{label}</p>
              <p className="mt-2 text-sm text-slate-700">{fallbackText(value)}</p>
            </div>
          ))}
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
