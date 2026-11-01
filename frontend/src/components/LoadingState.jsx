export default function LoadingState({ rows = 4 }) {
  return (
    <div className="grid">
      {Array.from({ length: rows }).map((_, i) => (
        <div className="card" key={i}>
          <div className="skeleton" style={{ width: "40%", marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 72 }} />
        </div>
      ))}
    </div>
  );
}
