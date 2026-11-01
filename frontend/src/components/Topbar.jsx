import { useLocation } from "react-router-dom";

const TITLES = {
  "/": "Executive Dashboard",
  "/forecast": "Sales Forecast",
  "/analytics": "Sales Analytics",
  "/inventory": "Inventory & Demand",
  "/model": "Model Performance",
};

export default function Topbar() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] || "Workspace";
  return (
    <header className="topbar">
      <div className="topbar-crumb">
        <span>Retail operations</span>
        <span aria-hidden="true">/</span>
        <strong>{title}</strong>
      </div>
      <div className="topbar-meta">
        <span className="meta-chip">Calendar 2024</span>
        <span className="meta-chip">Holdout · December</span>
        <span className="meta-chip">INR · India</span>
      </div>
    </header>
  );
}
