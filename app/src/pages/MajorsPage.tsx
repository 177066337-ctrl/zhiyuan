import { useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { FilterPanel } from "../components/FilterPanel";
import { LoadingState } from "../components/LoadingState";
import { MajorCard } from "../components/MajorCard";
import { SearchInput } from "../components/SearchInput";
import { useMajors } from "../hooks/useMajors";
import { useWishlist } from "../hooks/useWishlist";
import type { MajorFilter } from "../types";
import { filterMajors, getUniqueOptions } from "../utils/filters";

const INITIAL_FILTER: MajorFilter = {
  keyword: "",
  majorCode: "",
  degreeLevel: "",
  majorDiscipline: "",
  majorCategory: "",
};

export function MajorsPage() {
  const { data, loading, error } = useMajors();
  const wishlist = useWishlist();
  const [filter, setFilter] = useState<MajorFilter>(INITIAL_FILTER);
  const [visibleCount, setVisibleCount] = useState(50);

  const filtered = useMemo(() => filterMajors(data, filter), [data, filter]);
  const activeFilters = [
    filter.keyword ? `名称：${filter.keyword}` : "",
    filter.majorCode ? `代码：${filter.majorCode}` : "",
    filter.degreeLevel ? `层次：${filter.degreeLevel}` : "",
    filter.majorDiscipline ? `门类：${filter.majorDiscipline}` : "",
    filter.majorCategory ? `专业类：${filter.majorCategory}` : "",
  ].filter(Boolean);

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <EmptyState title="专业数据加载失败" description={error} />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">专业查询</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          当前共加载 {data.length} 条专业数据，支持按名称、代码、门类和专业类组合筛选。
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <SearchInput
            value={filter.keyword}
            onChange={(keyword) => {
              setVisibleCount(50);
              setFilter((current) => ({ ...current, keyword }));
            }}
            placeholder="搜索专业名称、门类或专业类"
          />
          <SearchInput
            value={filter.majorCode}
            onChange={(majorCode) => {
              setVisibleCount(50);
              setFilter((current) => ({ ...current, majorCode }));
            }}
            placeholder="搜索专业代码"
          />
        </div>
      </section>

      <FilterPanel
        title="专业筛选"
        resultSummary={`已筛选出 ${filtered.length} 个专业`}
        activeFilters={activeFilters}
        fields={[
          { label: "本科 / 专科", value: filter.degreeLevel, onChange: (degreeLevel) => setFilter((current) => ({ ...current, degreeLevel })), options: getUniqueOptions(data.map((item) => item.degree_level)) },
          { label: "门类 / 大类", value: filter.majorDiscipline, onChange: (majorDiscipline) => setFilter((current) => ({ ...current, majorDiscipline })), options: getUniqueOptions(data.map((item) => item.major_discipline)) },
          { label: "专业类", value: filter.majorCategory, onChange: (majorCategory) => setFilter((current) => ({ ...current, majorCategory })), options: getUniqueOptions(data.map((item) => item.major_category)) },
        ]}
        onReset={() => {
          setVisibleCount(50);
          setFilter(INITIAL_FILTER);
        }}
      />

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">已显示 {Math.min(visibleCount, filtered.length)} / {filtered.length} 个专业</p>
          {wishlist.message ? <p className="text-sm text-emerald-700">{wishlist.message}</p> : null}
        </div>

        {filtered.length === 0 ? (
          <EmptyState title="没有找到符合条件的专业" description="请尝试减少筛选条件或更换关键词。" />
        ) : (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              {filtered.slice(0, visibleCount).map((major) => (
                <MajorCard
                  key={major.major_id}
                  major={major}
                  collected={wishlist.isCollected(major.major_id)}
                  onCollect={wishlist.addMajor}
                />
              ))}
            </div>
            {visibleCount < filtered.length ? (
              <button
                type="button"
                onClick={() => setVisibleCount((count) => count + 50)}
                className="mx-auto block rounded-full bg-brand-600 px-5 py-3 text-sm font-medium text-white"
              >
                加载更多
              </button>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
