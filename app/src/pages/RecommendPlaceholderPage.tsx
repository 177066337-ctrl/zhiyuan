import { Disclaimer } from "../components/Disclaimer";

export function RecommendPlaceholderPage() {
  const steps = [
    "第一步：结构化录取最低分和最低位次",
    "第二步：接入一分一段表",
    "第三步：接入招生计划",
    "第四步：开放冲稳保辅助分析",
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">志愿推荐功能建设中</h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">
          当前版本尚未接入结构化录取分数、位次、一分一段表和招生计划数据，因此暂不提供冲稳保推荐。后续完成
          admissions、rank tables 和 plans 等核心数据后，才会开放基于历史数据的辅助分析。
        </p>
      </section>

      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <h2 className="text-lg font-semibold text-slate-900">后续规划</h2>
        <ol className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
          {steps.map((step) => (
            <li key={step} className="rounded-2xl bg-slate-50 px-4 py-3">
              {step}
            </li>
          ))}
        </ol>
      </section>

      <Disclaimer />
    </div>
  );
}
