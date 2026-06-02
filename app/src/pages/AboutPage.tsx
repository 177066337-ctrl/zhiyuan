import { Disclaimer } from "../components/Disclaimer";

export function AboutPage() {
  const dataSources = [
    "全国普通高等学校名单",
    "普通高等学校本科专业目录",
    "普通高等学校高等职业教育（专科）专业目录",
    "985 工程学校名单",
    "211 工程学校名单",
    "第二轮“双一流”建设高校及建设学科名单",
  ];

  const supported = ["院校查询", "专业查询", "985/211/双一流筛选", "收藏与导出"];
  const unsupported = ["冲稳保推荐", "录取概率", "历年分数线", "历年位次", "招生计划"];
  const limits = [
    "院校类型目前为名称关键词辅助分类，不代表权威院校分类结论。",
    "部分军队院校未包含在当前底表中，因此标签统计并非完整覆盖。",
    "部分学校的办学性质仍待进一步核对。",
    "专业选科要求、专业简介、学位和学制等字段尚未完全结构化。",
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-soft">
        <h1 className="text-2xl font-bold text-slate-900">数据说明</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
          这个工具当前定位为高考志愿填报的辅助查询工具，适合先查院校、查专业、做收藏和基础对比，不提供录取结果判断。
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
            <h2 className="text-lg font-semibold text-slate-900">当前不支持</h2>
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
          <h2 className="text-lg font-semibold text-slate-900">数据来源</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
            {dataSources.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-slate-900">当前局限</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">
            {limits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <Disclaimer />
    </div>
  );
}
