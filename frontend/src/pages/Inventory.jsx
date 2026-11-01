import Header from "../components/Header";
import DataTable from "../components/DataTable";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

export default function Inventory() {
  const { data, loading, error } = useApi(() => api.inventory(), []);
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page">
      <Header
        kicker="Operations"
        title="Inventory & Demand"
        subtitle="Categories with thinner stock cover while the 30-day sales outlook stays relatively high."
      />
      <div className="grid three">
        <div className="card status-card needs">
          <h3 className="risk-Needs">Needs attention</h3>
          <p className="note">Fewer days of stock than most categories, and a higher 30-day sales forecast.</p>
        </div>
        <div className="card status-card watch">
          <h3 className="risk-Watch">Watch</h3>
          <p className="note">Either stock cover is lower than most, or the forecast is higher than most — not both.</p>
        </div>
        <div className="card status-card ok">
          <h3 className="risk-In">In good shape</h3>
          <p className="note">Stock cover and the sales forecast are both in line with other categories.</p>
        </div>
      </div>
      <div className="card">
        <h3>Category view</h3>
        <DataTable
          rows={data.table}
          columns={[
            { key: "Category", label: "Category" },
            { key: "avg_stock", label: "Typical stock (units)", type: "num" },
            { key: "typical_daily_sales", label: "Typical daily sales (units)", type: "num" },
            { key: "days_of_stock", label: "Days of stock", type: "num" },
            { key: "Forecasted_Revenue", label: "30-day forecast", type: "inr" },
            { key: "status", label: "Status", type: "status" },
            { key: "why", label: "Why" },
          ]}
        />
        <p className="note">{data.plain_rule}</p>
        <p className="note">{data.note}</p>
      </div>
    </div>
  );
}
