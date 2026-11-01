import { Area, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { inr } from "../utils/format";
import { formatChartDate, rupeeAxis, spacedDateTicks, spanDays } from "../utils/charts";

export default function ForecastChart({
  data,
  title = "Actual vs forecasted revenue",
  subtitle,
  height = 320,
}) {
  const axis = rupeeAxis(data, ["Actual", "Forecast"], { fromZero: false });
  const ticks = spacedDateTicks(data, "Date", 6);
  const days = spanDays(data, "Date");
  return (
    <div className="card chart-card">
      <div className="chart-card-head">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p className="chart-card-sub">{subtitle}</p> : null}
        </div>
        <div className="chart-legend-key" aria-hidden="true">
          <span><i className="swatch actual" /> Actual</span>
          <span><i className="swatch forecast" /> Forecast</span>
        </div>
      </div>
      <div style={{ height }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 12, right: 16, left: 4, bottom: 8 }}>
            <defs>
              <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1a4a6e" stopOpacity={0.16} />
                <stop offset="100%" stopColor="#1a4a6e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#edf1f5" vertical={false} />
            <XAxis
              dataKey="Date"
              ticks={ticks}
              interval={0}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#5b6b78" }}
              tickFormatter={(value) => formatChartDate(value, days)}
            />
            <YAxis
              domain={axis.domain}
              ticks={axis.ticks}
              tickCount={axis.tickCount}
              width={axis.width}
              axisLine={false}
              tickLine={false}
              tickFormatter={axis.tickFormatter}
              tick={{ fontSize: 11, fill: "#5b6b78" }}
              allowDecimals={false}
            />
            <Tooltip
              cursor={{ stroke: "#c5d0da", strokeDasharray: "4 4" }}
              content={<ChartTooltip />}
            />
            <Legend content={() => null} />
            <Area type="monotone" dataKey="Actual" stroke="none" fill="url(#actualFill)" legendType="none" tooltipType="none" />
            <Line type="monotone" dataKey="Actual" stroke="#0d2c44" dot={false} strokeWidth={2.4} />
            <Line type="monotone" dataKey="Forecast" stroke="#1f6f5b" dot={false} strokeWidth={2.4} strokeDasharray="6 4" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const shown = payload.filter((item) => item.value != null && item.stroke && item.stroke !== "none");
  if (!shown.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{formatChartDate(label, 30)}</div>
      {(shown).map((item) => (
        <div key={item.dataKey} className="chart-tooltip-row">
          <span className="dot" style={{ background: item.color }} />
          <span>{item.dataKey}</span>
          <strong>{inr(item.value)}</strong>
        </div>
      ))}
    </div>
  );
}
