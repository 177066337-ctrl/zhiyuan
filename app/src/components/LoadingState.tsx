export function LoadingState() {
  return (
    <div className="rounded-3xl bg-white px-6 py-10 text-center shadow-soft">
      <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand-500" />
      <p className="mt-4 text-sm text-slate-600">正在加载数据...</p>
    </div>
  );
}
