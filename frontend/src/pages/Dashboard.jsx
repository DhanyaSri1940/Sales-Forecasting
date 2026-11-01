import ForecastChart from "../components/ForecastChart";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";

export default function Dashboard() {
  const { data, loading, error } = useApi(() => api.dashboard(), []);
  if (loading) return <LoadingState rows={2} />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="dash">
      <header className="dash-hero">
        <div>
          <p className="kicker">Executive overview</p>
          <h2>Sales versus forecast</h2>
          <p className="dash-lead">
            December holdout: recorded invoice revenue compared with the model forecast.
            Simulated Indian FMCG retail, 2024.
          </p>
        </div>
        <div className="dash-pills">
          <span className="dash-pill">Calendar 2024</span>
          <span className="dash-pill">Holdout · December</span>
          <span className="dash-pill">Date × Category</span>
        </div>
      </header>

      <ForecastChart
        data={data.test_actual_vs_forecast}
        title="Actual vs forecasted revenue"
        subtitle="Daily totals across all categories. The vertical scale is fitted to this window."
        height={380}
      />

      <section className="dash-insights-panel">
        <div className="dash-insights-head">
          <h3>Key business insights</h3>
          <p>Taken from the full-year invoice file and the December holdout.</p>
        </div>
        <ol className="dash-insights">
          {data.insights.map((line, index) => (
            <li key={index} className="dash-insight">
              <span className="dash-insight-index">{String(index + 1).padStart(2, "0")}</span>
              <p>{line}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
