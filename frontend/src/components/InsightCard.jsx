export default function InsightCard({ title, children }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="insight">{children}</div>
    </div>
  );
}
