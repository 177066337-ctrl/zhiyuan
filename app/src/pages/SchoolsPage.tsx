import { useMemo, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { FilterPanel } from "../components/FilterPanel";
import { LoadingState } from "../components/LoadingState";
import { SchoolCard } from "../components/SchoolCard";
import { SearchInput } from "../components/SearchInput";
import { useSchools } from "../hooks/useSchools";
import { useWishlist } from "../hooks/useWishlist";
import type { SchoolFilter } from "../types";
import { filterSchools, getUniqueOptions } from "../utils/filters";
import { formatCategory } from "../utils/text";

const INITIAL_FILTER: SchoolFilter = {
  keyword: "",
  province: "",
  city: "",
  schoolLevel: "",
  ownership: "",
  schoolType: "",
  tag: "",
};

export function SchoolsPage() {
  const { data, loading, error } = useSchools();
  const wishlist = useWishlist();
  const [filter, setFilter] = useState<SchoolFilter>(INITIAL_FILTER);
  const [visibleCount, setVisibleCount] = useState(50);

  const filtered = useMemo(() => filterSchools(data, filter), [data, filter]);
  const activeFilters = [
    filter.keyword ? `关键词：${filter.keyword}` : "",
    filter.province ? `省份：${filter.province}` : "",
    filter.city ? `城市：${filter.city}` : "",
    filter.schoolLevel ? `层次：${filter.schoolLevel}` : "",
    filter.ownership ? `性质：${filter.ownership}` : "",
    filter.schoolType ? `类型：${formatCategory(filter.schoolType)}` : "",
    filter.tag ? `标签：${filter.tag}` : "",
  ].filter(Boolean);

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <EmptyState title="院校数据加载失败" description={error} />;
  }

  const provinces = getUniqueOptions(data.map((item) => item.province));
  const cities = getUniqueOptions(data.map((item) => item.city));
  const schoolLevels = getUniqueOptions(data.map((item) => item.school_level));
  const ownerships = getUniqueOptions(data.map((item) => item.ownership));
  const schoolTypes = getUniqueOptions(data.map((item) => item.school_type));
  const tags = getUniqueOptions(data.flatMap((item) => item.tags ?? []));

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">院校查询</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          当前共加载 {data.length} 条院校数据，支持名称搜索、地区筛选、层次筛选和 985/211/双一流标签筛选。
        </p>
        <div className="mt-4">
          <SearchInput
            value={filter.keyword}
            onChange={(value) => {
              setVisibleCount(50);
              setFilter((current) => ({ ...current, keyword: value }));
            }}
            placeholder="搜索院校名称、省份或城市"
          />
        </div>
      </section>

      <FilterPanel
        title="院校筛选"
        resultSummary={`已筛选出 ${filtered.length} 所院校`}
        activeFilters={activeFilters}
        fields={[
          { label: "省份", value: filter.province, onChange: (province) => setFilter((current) => ({ ...current, province })), options: provinces },
          { label: "城市", value: filter.city, onChange: (city) => setFilter((current) => ({ ...current, city })), options: cities },
          { label: "院校层次", value: filter.schoolLevel, onChange: (schoolLevel) => setFilter((current) => ({ ...current, schoolLevel })), options: schoolLevels },
          { label: "办学性质", value: filter.ownership, onChange: (ownership) => setFilter((current) => ({ ...current, ownership })), options: ownerships },
          { label: "院校类型", value: filter.schoolType, onChange: (schoolType) => setFilter((current) => ({ ...current, schoolType })), options: schoolTypes },
          { label: "标签", value: filter.tag, onChange: (tag) => setFilter((current) => ({ ...current, tag })), options: tags.filter((tag) => ["985", "211", "双一流"].includes(tag)) },
        ]}
        onReset={() => {
          setVisibleCount(50);
          setFilter(INITIAL_FILTER);
        }}
      />

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">已显示 {Math.min(visibleCount, filtered.length)} / {filtered.length} 所</p>
          {wishlist.message ? <p className="text-sm text-emerald-700">{wishlist.message}</p> : null}
        </div>

        {filtered.length === 0 ? (
          <EmptyState title="没有找到符合条件的院校" description="请尝试减少筛选条件或更换关键词。" />
        ) : (
          <>
            <div className="grid gap-4 lg:grid-cols-2">
              {filtered.slice(0, visibleCount).map((school) => (
                <SchoolCard
                  key={school.school_id}
                  school={school}
                  collected={wishlist.isCollected(school.school_id)}
                  onCollect={wishlist.addSchool}
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
