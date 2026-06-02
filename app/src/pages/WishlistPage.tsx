import { EmptyState } from "../components/EmptyState";
import { useWishlist } from "../hooks/useWishlist";
import { copyText, exportWishlistFile } from "../utils/storage";

export function WishlistPage() {
  const wishlist = useWishlist();

  const schoolItems = wishlist.items.filter((item) => item.type === "school");
  const majorItems = wishlist.items.filter((item) => item.type === "major");

  async function handleCopy() {
    const content = wishlist.items
      .map((item, index) => `${index + 1}. [${item.type === "school" ? "院校" : "专业"}] ${item.title} - ${item.subtitle}`)
      .join("\n");
    if (!content) {
      return;
    }
    const ok = await copyText(content);
    if (!ok) {
      window.alert("复制失败，请稍后重试。");
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl bg-white p-5 shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">我的收藏</h1>
            <p className="mt-2 text-sm text-slate-600">使用 localStorage 保存，支持导出和复制。</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
            >
              复制文本
            </button>
            <button
              type="button"
              onClick={() => exportWishlistFile(wishlist.items)}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
            >
              导出 JSON
            </button>
            <button
              type="button"
              onClick={wishlist.clearAll}
              className="rounded-full bg-rose-50 px-4 py-2 text-sm text-rose-700"
            >
              清空收藏
            </button>
          </div>
        </div>
        {wishlist.message ? <p className="mt-3 text-sm text-emerald-700">{wishlist.message}</p> : null}
      </section>

      {wishlist.items.length === 0 ? (
        <EmptyState title="还没有收藏内容" description="你可以在院校页或专业页点击“收藏”按钮，稍后回来查看。" />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-3xl bg-white p-5 shadow-soft">
            <h2 className="text-lg font-semibold text-slate-900">收藏院校 ({schoolItems.length})</h2>
            <p className="mt-1 text-sm text-slate-500">用于后续整理志愿意向学校。</p>
            <div className="mt-4 space-y-3">
              {schoolItems.map((item) => (
                <div key={item.id} className="rounded-2xl bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">{item.title}</p>
                      <p className="mt-1 text-sm text-slate-500">{item.subtitle}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => wishlist.removeItem(item.id)}
                      className="text-sm text-rose-600"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-3xl bg-white p-5 shadow-soft">
            <h2 className="text-lg font-semibold text-slate-900">收藏专业 ({majorItems.length})</h2>
            <p className="mt-1 text-sm text-slate-500">用于对比关注专业及其培养层次。</p>
            <div className="mt-4 space-y-3">
              {majorItems.map((item) => (
                <div key={item.id} className="rounded-2xl bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">{item.title}</p>
                      <p className="mt-1 text-sm text-slate-500">{item.subtitle}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => wishlist.removeItem(item.id)}
                      className="text-sm text-rose-600"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
