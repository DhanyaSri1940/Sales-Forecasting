export default function KPICard({ label, value, hint, tone }) {
  return (
    <div className={`card kpi${tone ? ` ${tone}` : ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}
