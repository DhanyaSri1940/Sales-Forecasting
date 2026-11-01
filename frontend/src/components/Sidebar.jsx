import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Executive Dashboard", icon: DashboardIcon },
  { to: "/forecast", label: "Sales Forecast", icon: ForecastIcon },
  { to: "/analytics", label: "Sales Analytics", icon: AnalyticsIcon },
  { to: "/inventory", label: "Inventory & Demand", icon: InventoryIcon },
  { to: "/model", label: "Model Performance", icon: ModelIcon },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">FI</div>
        <div>
          <h1>FMCG Intelligence</h1>
          <p>Sales forecasting & retail analytics</p>
        </div>
      </div>
      <nav>
        <div className="nav-group-label">Workspace</div>
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === "/"} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            <l.icon />
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-foot">
        <strong>Simulated India retail · 2024</strong>
        <span>Invoice-level FMCG file. Forecasts are model outputs, not commitments.</span>
      </div>
    </aside>
  );
}

function DashboardIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="1.5" y="1.5" width="5.5" height="6" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="9" y="1.5" width="5.5" height="3.5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="9" y="7" width="5.5" height="7.5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="1.5" y="9.5" width="5.5" height="5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}
function ForecastIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 12.5 6 7.5 9 10l5-7" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      <path d="M11 3h3v3" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}
function AnalyticsIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M3 13V7M8 13V3M13 13V9" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
function InventoryIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2.5 5.5 8 2.5l5.5 3V13a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1V5.5Z" stroke="currentColor" strokeWidth="1.4" />
      <path d="M8 7.5v6" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}
function ModelIcon() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="4" r="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="3.5" cy="12" r="2" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="12.5" cy="12" r="2" stroke="currentColor" strokeWidth="1.4" />
      <path d="M6.4 5.4 4.6 10.1M9.6 5.4l1.8 4.7" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}
