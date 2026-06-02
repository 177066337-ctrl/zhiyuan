import { Outlet } from "react-router-dom";
import { BottomNav } from "./BottomNav";
import { Header } from "./Header";

export function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header />
      <main className="mx-auto max-w-container px-4 pb-28 pt-6 lg:px-6 lg:pb-10">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
