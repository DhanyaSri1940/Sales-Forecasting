import { useState } from "react";
import Header from "../components/Header";
import FilterToolbar from "../components/FilterToolbar";
import DataTable from "../components/DataTable";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { FILTER_OPTIONS, inr } from "../utils/format";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatChartDate, monthStartTicks, rupeeAxis, spanDays } from "../utils/charts";

export default function Analytics() {
  const [filters, setFilters] = useState({ city: "", category: "", brand: "", channel: "", store_format: "", payment_mode: "" });
  const key = JSON.stringify(filters);
  const cats = useApi(() => api.categories(filters), [key]);
  const cities = useApi(() => api.cities(filters), [key]);
  const brands = useApi(() => api.brands(filters), [key]);
  const channels = useApi(() => api.channels(filters), [key]);
  const formats = useApi(() => api.storeFormats(filters), [key]);
  const pay = useApi(() => api.paymentModes(filters), [key]);
  const loyalty = useApi(() => api.loyalty(filters), [key]);
  const daily = useApi(() => api.daily(filters), [key]);

  const loading = [cats, cities, brands, channels, formats, pay, loyalty, daily].some((x) => x.loading);
  const error = [cats, cities, brands, channels, formats, pay, loyalty, daily].find((x) => x.error)?.error;
  const set = (field) => (e) => setFilters((f) => ({ ...f, [field]: e.target.value }));

  return (
    <div className="page">
      <Header
        kicker="Performance mix"
        title="Sales Analytics"
        subtitle="How recorded sales split across categories, cities, brands, channels, and store formats."
      />
      <FilterToolbar
        fields={[
          { key: "city", label: "City", placeholder: "All cities", value: filters.city, options: FILTER_OPTIONS.cities, onChange: set("city") },
          { key: "category", label: "Category", placeholder: "All categories", value: filters.category, options: FILTER_OPTIONS.categories, onChange: set("category") },
          { key: "brand", label: "Brand", placeholder: "All brands", value: filters.brand, options: FILTER_OPTIONS.brands, onChange: set("brand") },
          { key: "channel", label: "Channel", placeholder: "All channels", value: filters.channel, options: FILTER_OPTIONS.channels, onChange: set("channel") },
          { key: "store_format", label: "Store format", placeholder: "All formats", value: filters.store_format, options: FILTER_OPTIONS.storeFormats, onChange: set("store_format") },
          { key: "payment_mode", label: "Payment", placeholder: "All modes", value: filters.payment_mode, options: FILTER_OPTIONS.paymentModes, onChange: set("payment_mode") },
        ]}
      />
      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> : (
        <>
          <SimpleBar title="Revenue by category" data={cats.data} x="Category" />
          <div className="card">
            <h3>Daily revenue under current filters</h3>
            <DailyBars data={daily.data || []} />
          </div>
          <SimpleBar title="Revenue by city" data={cities.data} x="City" />
          <SimpleBar title="Revenue by brand" data={brands.data} x="Brand" />
          <div className="grid three">
            <SimpleBar title="Channel mix" data={channels.data} x="Channel" compact />
            <SimpleBar title="Store format mix" data={formats.data} x="Store_Format" compact />
            <SimpleBar title="Payment mode mix" data={pay.data} x="Payment_Mode" compact />
          </div>
          <div className="card">
            <h3>Loyalty vs non-loyalty</h3>
            <DataTable
              rows={(loyalty.data || []).map((r) => ({ ...r, Loyalty_Flag: r.Loyalty_Flag === 1 || r.Loyalty_Flag === "1" ? "Loyalty" : "Non-loyalty" }))}
              columns={[
                { key: "Loyalty_Flag", label: "Segment" },
                { key: "Revenue", label: "Revenue", type: "inr" },
                { key: "Revenue_Share_%", label: "Share", type: "pct" },
                { key: "Invoices", label: "Invoices", type: "num" },
              ]}
            />
            <p className="note">Customer age is missing for part of the file and is not imputed. Gender missing values are excluded from gender-specific claims.</p>
          </div>
        </>
      )}
    </div>
  );
}

function SimpleBar({ title, data, x, compact }) {
  const axis = rupeeAxis(data, ["Revenue"]);
  return (
    <div className="card">
      <h3>{title}</h3>
      <div style={{ height: compact ? 200 : 260 }}>
        <ResponsiveContainer>
          <BarChart data={data || []} margin={{ top: 8, right: 8, left: 4, bottom: 8 }}>
            <XAxis dataKey={x} tick={{ fontSize: 11, fill: "#5a6b78" }} interval={0} axisLine={false} tickLine={false} />
            <YAxis
              domain={axis.domain}
              tickCount={axis.tickCount}
              width={axis.width}
              tickFormatter={axis.tickFormatter}
              tick={{ fontSize: 11, fill: "#5a6b78" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip cursor={{ fill: "rgba(13, 44, 68, 0.04)" }} formatter={(v) => inr(v)} />
            <Bar dataKey="Revenue" fill="#1a4a6e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DailyBars({ data }) {
  const axis = rupeeAxis(data, ["Revenue"]);
  const ticks = monthStartTicks(data, "Date");
  const days = spanDays(data, "Date");
  return (
    <div style={{ height: 240 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 8 }}>
          <XAxis
            dataKey="Date"
            ticks={ticks}
            interval={0}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: "#5a6b78" }}
            tickFormatter={(value) => formatChartDate(value, days)}
          />
          <YAxis
            domain={axis.domain}
            tickCount={axis.tickCount}
            width={axis.width}
            axisLine={false}
            tickLine={false}
            tickFormatter={axis.tickFormatter}
            tick={{ fontSize: 11, fill: "#5a6b78" }}
          />
          <Tooltip cursor={{ fill: "rgba(13, 44, 68, 0.04)" }} labelFormatter={(value) => formatChartDate(value, 30)} formatter={(v) => inr(v)} />
          <Bar dataKey="Revenue" fill="#3d6f91" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
