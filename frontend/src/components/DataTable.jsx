import { inr, num, pct } from "../utils/format";

export default function DataTable({ rows, columns }) {
  if (!rows?.length) return <div className="empty">No rows for the current filters.</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c.key} className={c.className ? c.className(row) : undefined}>
                  {formatCell(row[c.key], c.type)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value, type) {
  if (type === "inr") return inr(value);
  if (type === "num") return num(value);
  if (type === "num1") return num(value, 1);
  if (type === "num2") return num(value, 2);
  if (type === "pct") return pct(value);
  if (type === "pct100") return pct(value * 100);
  if (type === "status") {
    const text = String(value ?? "—");
    const kind = text.startsWith("Needs") ? "badge-needs" : text.startsWith("Watch") ? "badge-watch" : "badge-ok";
    return <span className={`badge ${kind}`}>{text}</span>;
  }
  return value ?? "—";
}
