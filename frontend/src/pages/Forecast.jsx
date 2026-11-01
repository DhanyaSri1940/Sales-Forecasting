import { useMemo, useState } from "react";
import Header from "../components/Header";
import KPICard from "../components/KPICard";
import FilterToolbar from "../components/FilterToolbar";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { FILTER_OPTIONS, downloadCsv, inr, pct } from "../utils/format";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { formatChartDate, rupeeAxis, horizonDateTicks } from "../utils/charts";

export default function Forecast() {
  const [filters, setFilters] = useState({ horizon: "", city: "", category: "", brand: "", channel: "", store_format: "" });
  const { data, loading, error } = useApi(
    () => api.forecast({ ...filters, horizon: filters.horizon || "14" }),
    [JSON.stringify(filters)]
  );

  const chartData = useMemo(() => {
    if (!data) return [];
    const hist = data.historical.map((r) => ({ Date: r.Date, Actual: r.Actual_Revenue, Forecast: null }));
    const fc = data.forecast.map((r) => ({ Date: r.Date, Actual: null, Forecast: r.Forecasted_Revenue }));
    if (hist.length) {
      const last = hist[hist.length - 1];
      hist[hist.length - 1] = { ...last, Forecast: last.Actual };
    }
    return [...hist, ...fc];
  }, [data]);
  const axis = rupeeAxis(chartData, ["Actual", "Forecast"], { fromZero: false });
  const ticks = horizonDateTicks(chartData, data?.horizon);
  const growth = Number(data?.forecasted_growth_pct);

  return (
    <div className="page">
      <Header
        kicker="Forward view"
        title="Sales Forecast"
        subtitle="Expected sales for the next 7, 14, or 30 days. Narrow by city, category, brand, channel, or store format."
        extra={<button className="btn" onClick={() => data && downloadCsv("forecast.csv", data.forecast)}>Download CSV</button>}
      />
      <FilterToolbar
        fields={[
          { key: "horizon", label: "Horizon", placeholder: "14 days (default)", value: filters.horizon, options: [{ value: "7", label: "7 days" }, { value: "14", label: "14 days" }, { value: "30", label: "30 days" }], onChange: (e) => setFilters((f) => ({ ...f, horizon: e.target.value })) },
          { key: "city", label: "City", placeholder: "All cities", value: filters.city, options: FILTER_OPTIONS.cities, onChange: set("city", setFilters) },
          { key: "category", label: "Category", placeholder: "All categories", value: filters.category, options: FILTER_OPTIONS.categories, onChange: set("category", setFilters) },
          { key: "brand", label: "Brand", placeholder: "All brands", value: filters.brand, options: FILTER_OPTIONS.brands, onChange: set("brand", setFilters) },
          { key: "channel", label: "Channel", placeholder: "All channels", value: filters.channel, options: FILTER_OPTIONS.channels, onChange: set("channel", setFilters) },
          { key: "store_format", label: "Store format", placeholder: "All formats", value: filters.store_format, options: FILTER_OPTIONS.storeFormats, onChange: set("store_format", setFilters) },
        ]}
      />
      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> : (
        <>
          <div className="grid four">
            <KPICard label="Expected sales" value={inr(data.forecast_total)} hint={`Forecast for the next ${data.horizon} days`} />
            <KPICard label="Recent actual sales" value={inr(data.previous_period_actual)} hint={`Recorded sales in the last ${data.horizon} days`} />
            <KPICard
              label="Difference"
              value={inr(data.change_from_previous_period)}
              hint="Expected sales minus recent actual sales"
              tone={Number(data.change_from_previous_period) >= 0 ? "up" : "down"}
            />
            <KPICard
              label="Expected change"
              value={pct(data.forecasted_growth_pct)}
              hint={`Compared with the last ${data.horizon} days`}
              tone={growth >= 0 ? "up" : "down"}
            />
          </div>
          <div className="card">
            <div className="chart-card-head">
              <div>
                <h3>Historical revenue and forecasted revenue</h3>
                <p className="chart-card-sub">Last {data.horizon} actual days plus the {data.horizon}-day forecast. Scale is fitted to this window.</p>
              </div>
              <div className="chart-legend-key" aria-hidden="true">
                <span><i className="swatch actual" /> Actual</span>
                <span><i className="swatch forecast" /> Forecast</span>
              </div>
            </div>
            <div style={{ height: 340 }}>
              <ResponsiveContainer>
                <LineChart key={`h-${data.horizon}-${JSON.stringify(data.filters)}`} data={chartData} margin={{ top: 8, right: 16, left: 4, bottom: 24 }}>
                  <CartesianGrid stroke="#edf1f5" vertical={false} />
                  <XAxis
                    dataKey="Date"
                    ticks={ticks}
                    interval={0}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 10, fill: "#5a6b78" }}
                    angle={-40}
                    textAnchor="end"
                    height={48}
                    tickFormatter={(value) => formatChartDate(value)}
                  />
                  <YAxis
                    domain={axis.domain}
                    ticks={axis.ticks}
                    tickCount={axis.tickCount}
                    width={axis.width}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={axis.tickFormatter}
                    tick={{ fontSize: 11, fill: "#5a6b78" }}
                    allowDecimals={false}
                  />
                  <Tooltip
                    cursor={{ stroke: "#c5d0da", strokeDasharray: "4 4" }}
                    labelFormatter={(value) => formatChartDate(value)}
                    formatter={(v) => inr(v)}
                  />
                  <Line type="monotone" dataKey="Actual" stroke="#0d2c44" dot={false} strokeWidth={2.2} connectNulls={false} />
                  <Line type="monotone" dataKey="Forecast" stroke="#1f6f5b" dot={false} strokeWidth={2.2} strokeDasharray="6 4" connectNulls={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="note">
              Tick marks are daily (7-day), every 2 days (14-day), or every 5 days (30-day). The vertical axis does not start at ₹0 so day-to-day movement stays readable.
            </p>
            <p className="note">{data.recursive_note}</p>
            {data.allocation_note ? <p className="note">{data.allocation_note}</p> : null}
          </div>
        </>
      )}
    </div>
  );
}

function set(key, setFilters) {
  return (e) => setFilters((f) => ({ ...f, [key]: e.target.value }));
}
