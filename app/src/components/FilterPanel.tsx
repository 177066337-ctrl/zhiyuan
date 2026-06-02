import { useState } from "react";

interface FilterFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}

interface FilterPanelProps {
  title: string;
  fields: FilterFieldProps[];
  onReset: () => void;
  resultSummary?: string;
  activeFilters?: string[];
}

export function FilterPanel({
  title,
  fields,
  onReset,
  resultSummary,
  activeFilters = [],
}: FilterPanelProps) {
  const [open, setOpen] = useState(false);

  return (
    <section className="rounded-3xl bg-white p-4 shadow-soft">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <p className="text-xs text-slate-500">支持组合筛选，移动端可折叠</p>
          {resultSummary ? <p className="mt-1 text-sm font-medium text-brand-700">{resultSummary}</p> : null}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-600"
          >
            重置
          </button>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 lg:hidden"
          >
            {open ? "收起筛选" : "展开筛选"}
          </button>
        </div>
      </div>

      {activeFilters.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {activeFilters.map((filter) => (
            <span
              key={filter}
              className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700"
            >
              {filter}
            </span>
          ))}
        </div>
      ) : null}

      <div className={`${open ? "mt-4 grid" : "hidden"} gap-3 lg:mt-4 lg:grid lg:grid-cols-2 xl:grid-cols-3`}>
        {fields.map((field) => (
          <label key={field.label} className="flex flex-col gap-2 text-sm text-slate-700">
            <span>{field.label}</span>
            <select
              value={field.value}
              onChange={(event) => field.onChange(event.target.value)}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-brand-500"
            >
              <option value="">全部</option>
              {field.options.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
    </section>
  );
}
