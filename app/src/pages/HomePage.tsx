import { Link } from "react-router-dom";
import { Disclaimer } from "../components/Disclaimer";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { useMajors } from "../hooks/useMajors";
import { useSchools } from "../hooks/useSchools";

export function HomePage() {
  const schoolsState = useSchools();
  const majorsState = useMajors();

  if (schoolsState.loading || majorsState.loading) {
    return <LoadingState />;
  }

  if (schoolsState.error || majorsState.error) {
    return (
      <EmptyState
        title="首页数据加载失败"
        description={schoolsState.error ?? majorsState.error ?? "请稍后重试。"}
      />
    );
  }

  const schools = schoolsState.data;
  const majors = majorsState.data;
  const stats = [
    { label: "院校总数", value: schools.length },
    { label: "专业总数", value: majors.length },
    { label: "985 院校", value: schools.filter((item) => item.is_985).length },
    { label: "211 院校", value: schools.filter((item) => item.is_211).length },
    { label: "双一流院校", value: schools.filter((item) => item.is_double_first_class).length },
    { label: "本科专业", value: majors.filter((item) => item.degree_level === "本科").length },
    { label: "专科专业", value: majors.filter((item) => item.degree_level === "专科").length },
  ];

  const quickLinks = [
    { title: "查院校", description: "按名称、省份、层次和标签筛选院校。", to: "/schools" },
    { title: "查专业", description: "按专业代码、门类和培养层次检索专业。", to: "/majors" },
    { title: "我的收藏", description: "集中查看、导出已收藏的院校和专业。", to: "/wishlist" },
    { title: "志愿推荐", description: "建设中，待录取数据结构化后开放。", to: "/recommend" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-brand-700 via-brand-600 to-accent-600 px-6 py-8 text-white shadow-soft">
        <p className="text-sm uppercase tracking-[0.25em] text-white/70">MVP</p>
        <h1 className="mt-3 text-3xl font-bold sm:text-4xl">高考志愿填报辅助工具</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-white/85 sm:text-base">
          基于院校名单、专业目录和院校标签构建。当前版本主要支持院校查询和专业查询，适合先做信息检索、收藏整理和初步对比。
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {quickLinks.map((item) => (
          <Link
            key={item.title}
            to={item.to}
            className="rounded-3xl bg-white p-5 shadow-soft transition hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">{item.title}</h2>
              {item.title === "志愿推荐" ? (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
                  建设中
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
          </Link>
        ))}
      </section>

      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">数据概览</h2>
            <p className="text-sm text-slate-500">动态读取当前结构化数据文件</p>
          </div>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {stats.map((item) => (
            <div key={item.label} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{item.value}</p>
            </div>
          ))}
        </div>
      </section>

      <Disclaimer />
    </div>
  );
}
