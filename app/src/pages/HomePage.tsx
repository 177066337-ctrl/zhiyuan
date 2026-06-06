import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Disclaimer } from "../components/Disclaimer";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { useMajors } from "../hooks/useMajors";
import { useSchools } from "../hooks/useSchools";
import type { ScoreLookupIndex } from "../types/scoreLookup";

function scoreLookupUrl(path: string) {
  return `${import.meta.env.BASE_URL}${path}`;
}

export function HomePage() {
  const schoolsState = useSchools();
  const majorsState = useMajors();
  const [scoreLookupIndex, setScoreLookupIndex] = useState<ScoreLookupIndex | null>(null);

  const schools = schoolsState.data;
  const majors = majorsState.data;
  const scoreLookupDatasets = scoreLookupIndex?.datasets ?? [];

  useEffect(() => {
    let active = true;

    fetch(scoreLookupUrl("data/score-lookup/index.json"), { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error("无法加载分数查询索引");
        }
        return (await response.json()) as ScoreLookupIndex;
      })
      .then((payload) => {
        if (active) {
          setScoreLookupIndex(payload);
        }
      })
      .catch(() => {
        if (active) {
          setScoreLookupIndex(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const qualityCounts = useMemo(() => {
    const counts = {
      verified: 0,
      warning: 0,
      candidate: 0,
      scoreOnly: 0,
    };

    for (const item of scoreLookupDatasets) {
      if (!item.is_public) {
        continue;
      }
      if (item.quality_status === "verified") {
        counts.verified += 1;
      } else if (item.quality_status === "warning") {
        counts.warning += 1;
      } else if (item.quality_status === "candidate") {
        counts.candidate += 1;
      } else if (item.quality_status === "score_only") {
        counts.scoreOnly += 1;
      }
    }

    return counts;
  }, [scoreLookupDatasets]);

  const stats = [
    { label: "院校总数", value: schools.length },
    { label: "专业总数", value: majors.length },
    { label: "985 院校", value: schools.filter((item) => item.is_985).length },
    { label: "211 院校", value: schools.filter((item) => item.is_211).length },
    {
      label: "双一流院校",
      value: schools.filter((item) => item.is_double_first_class).length,
    },
    {
      label: "本科专业",
      value: majors.filter((item) => item.degree_level === "本科").length,
    },
    {
      label: "专科专业",
      value: majors.filter((item) => item.degree_level === "专科").length,
    },
    {
      label: "候选数据集",
      value: scoreLookupDatasets.filter((item) => item.is_public).length,
    },
  ];

  const quickLinks = [
    {
      title: "查院校",
      description: "按院校名称、省份、层次、办学性质和标签快速筛选。",
      to: "/schools",
    },
    {
      title: "查专业",
      description: "按专业名称、专业代码、门类和本科/专科条件查询。",
      to: "/majors",
    },
    {
      title: "我的收藏",
      description: "保存感兴趣的院校和专业，后续继续对比查看。",
      to: "/wishlist",
    },
    {
      title: "按分数查志愿（全国候选试验版）",
      description: "已开放全国候选数据试查，部分数据尚未人工复核，请谨慎参考。",
      to: "/score-lookup",
    },
    {
      title: "志愿推荐建设中",
      description: "正式推荐算法、计划数据和人工复核仍在完善中。",
      to: "/recommend",
      badge: "建设中",
    },
  ];

  if (schoolsState.loading || majorsState.loading) {
    return <LoadingState />;
  }

  if (schoolsState.error || majorsState.error) {
    return (
      <EmptyState
        title="数据加载失败"
        description={schoolsState.error ?? majorsState.error ?? "请稍后重试。"}
      />
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-brand-700 via-brand-600 to-emerald-600 px-6 py-8 text-white shadow-soft">
        <p className="text-sm uppercase tracking-[0.25em] text-white/70">MVP</p>
        <h1 className="mt-3 text-3xl font-bold sm:text-4xl">高考志愿填报辅助工具</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-white/85 sm:text-base">
          当前版本优先提供院校查询、专业查询、收藏，以及全国候选历史录取参考查询。
          页面不会提供预测性结论或承诺式表述。
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {quickLinks.map((item) => (
          <Link
            key={item.title}
            to={item.to}
            className="rounded-3xl bg-white p-5 shadow-soft transition hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">{item.title}</h2>
              {item.badge ? (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
                  {item.badge}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
          </Link>
        ))}
      </section>

      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">数据概览</h2>
          <p className="text-sm text-slate-500">
            首页只加载基础查询数据和候选索引，不会默认拉取全国 admissions 大分片。
          </p>
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

      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <h2 className="text-lg font-semibold text-slate-900">全国候选试验版状态</h2>
        <p className="mt-1 text-sm text-slate-500">
          当前开放候选数据集 {scoreLookupDatasets.filter((item) => item.is_public).length} 个。
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl bg-emerald-50 p-4">
            <p className="text-sm text-emerald-700">已抽检通过</p>
            <p className="mt-2 text-2xl font-bold text-emerald-900">{qualityCounts.verified}</p>
          </div>
          <div className="rounded-2xl bg-sky-50 p-4">
            <p className="text-sm text-sky-700">未复核候选</p>
            <p className="mt-2 text-2xl font-bold text-sky-900">{qualityCounts.candidate}</p>
          </div>
          <div className="rounded-2xl bg-amber-50 p-4">
            <p className="text-sm text-amber-700">警示数据</p>
            <p className="mt-2 text-2xl font-bold text-amber-900">{qualityCounts.warning}</p>
          </div>
          <div className="rounded-2xl bg-slate-100 p-4">
            <p className="text-sm text-slate-700">仅分数参考</p>
            <p className="mt-2 text-2xl font-bold text-slate-900">{qualityCounts.scoreOnly}</p>
          </div>
        </div>
      </section>

      <Disclaimer />
    </div>
  );
}
