import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { inr } from "../utils/format";
import { formatChartDate, monthStartTicks, rupeeAxis, spanDays } from "../utils/charts";

export default function RevenueChart({ data, x = "Date", y = "Revenue", title = "Historical revenue" }) {
  const axis = rupeeAxis(data, [y]);
  const ticks = monthStartTicks(data, x);
  const days = spanDays(data, x);
  return (
    <div className="card">
      <h3>{title}</h3>
      <div style={{ height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
            <CartesianGrid stroke="#eef2f5" />
            <XAxis
              dataKey={x}
              ticks={ticks}
              interval={0}
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => formatChartDate(value, days)}
            />
            <YAxis
              domain={axis.domain}
              tickCount={axis.tickCount}
              width={axis.width}
              tickFormatter={axis.tickFormatter}
              tick={{ fontSize: 11 }}
            />
            <Tooltip labelFormatter={(value) => formatChartDate(value, 30)} formatter={(v) => inr(v)} />
            <Line type="monotone" dataKey={y} stroke="#1b4b73" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
