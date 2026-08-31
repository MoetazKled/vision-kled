import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api } from "../api";

const links = [
  { to: "/", label: "لوحة التحكم" },
  { to: "/leads", label: "العملاء والمحادثة" },
  { to: "/demos", label: "مواقع الديمو" },
  { to: "/products", label: "المنتجات" },
];

export function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  async function startTrial() {
    const lead = await api.trialLead();
    navigate(`/leads/${lead.id}`);
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          منصة
          <strong>Vision Kled</strong>
        </div>
        <button className="btn accent" onClick={() => void startTrial()}>
          ابدأ تجربة الآن
        </button>
        <nav>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="founder">
          المشرف الأعلى
          <br />
          Moetez Khaled
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
