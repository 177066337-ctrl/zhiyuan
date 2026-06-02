import { Link, NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "首页" },
  { to: "/schools", label: "院校" },
  { to: "/majors", label: "专业" },
  { to: "/wishlist", label: "收藏" },
  { to: "/about", label: "说明" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/70 bg-slate-50/90 backdrop-blur">
      <div className="mx-auto flex max-w-container items-center justify-between gap-6 px-4 py-4 lg:px-6">
        <Link to="/" className="min-w-0">
          <p className="truncate text-lg font-bold text-brand-700">高考志愿填报辅助工具</p>
          <p className="hidden text-xs text-slate-500 sm:block">基础检索型网页 MVP</p>
        </Link>
        <nav className="hidden items-center gap-2 lg:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-medium ${
                  isActive ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-white"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
