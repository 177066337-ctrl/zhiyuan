import { Disclaimer } from "../components/Disclaimer";

export function AboutPage() {
  const supported = [
    "全国院校查询",
    "全国专业查询",
    "985 / 211 / 双一流筛选",
    "收藏院校和专业",
    "全国候选录取数据试查",
    "部分数据支持分数换位次",
    "部分数据仅支持历史最低分查询",
  ];

  const qualityScope = [
    "福建 2023 历史类：已抽检通过，可查询。",
    "江西 2025 历史类：开放试查，抽检发现问题，请谨慎参考。",
    "其他候选省份：开放试查，暂未人工复核。",
  ];

  const unsupported = [
    "这不是正式志愿推荐系统",
    "不提供录取结果预测",
    "不保证所有省份、年份、科类、批次完整",
    "部分数据尚未人工复核",
    "需要 OCR 的资料暂未开放",
    "招生计划数据暂未正式接入",
    "2026 当年实时招生计划暂未完整接入",
  ];

  const notOpenYet = [
    "大部分需要 OCR 的数据",
    "subject_type = 未知 的数据",
    "failed 任务结果",
    "人工复核后仍不合格的数据",
    "16G 原始资料",
  ];

  const notes = [
    "“按分数查志愿（全国候选试验版）”会明确区分已抽检通过、未人工复核、抽检有问题和仅分数参考四类数据。",
    "冲、稳、保分组只是历史数据对比结果，不代表实际录取结果。",
    "没有 rank table 的数据集会自动降级为历史最低分参考，不做位次换算。",
    "结果仅供资料查看和历史参考，不构成录取承诺。",
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">数据说明</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
          当前版本以公开资料和已整理数据为基础，优先提供可回溯的基础查询体验。
          新增的“按分数查志愿（全国候选试验版）”已经开放全国候选数据，但不同数据集的质量状态并不一致，页面会显式提示风险。
        </p>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl bg-slate-50 p-4">
            <h2 className="text-lg font-semibold text-slate-900">当前支持</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
              {supported.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <h2 className="text-lg font-semibold text-slate-900">当前限制</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
              {unsupported.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">当前开放范围</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
            {qualityScope.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">暂不开放的数据</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
            {notOpenYet.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <h2 className="text-lg font-semibold text-slate-900">按分数查志愿试验版说明</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
          {notes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <Disclaimer />
    </div>
  );
}
