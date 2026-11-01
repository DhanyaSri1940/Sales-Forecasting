import { useState } from "react";
import Header from "../components/Header";
import DataTable from "../components/DataTable";
import InsightCard from "../components/InsightCard";
import KPICard from "../components/KPICard";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { featureLabel } from "../utils/format";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function ModelPerformance() {
  const { data, loading, error } = useApi(() => api.model(), []);
  const [question, setQuestion] = useState(
    "How does XGBoost compare with the baselines on the December holdout, and do training versus validation errors suggest overfitting?"
  );
  const [insight, setInsight] = useState(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    setBusy(true);
    try {
      setInsight(await api.insight(question));
    } catch (err) {
      setInsight({ answer: err.message, grounded: false });
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="page">
      <Header
        kicker="Model governance"
        title="Model Performance"
        subtitle="Holdout metrics from chronological validation. These are regression errors, not classification accuracy."
      />
      <div className="grid three">
        <KPICard label="Training MAE" value={fmt(data.xgboost_train.MAE)} hint={data.metric_explanations.MAE} />
        <KPICard label="Validation MAE" value={fmt(data.xgboost_validation.MAE)} hint="Used for early stopping only" />
        <KPICard label="Test MAE" value={fmt(data.xgboost_test.MAE)} hint="December holdout; unseen relative to training" />
      </div>
      {data.overfitting_note ? <p className="note">{data.overfitting_note}</p> : <p className="note">Training and validation errors are shown so overfitting can be inspected rather than hidden.</p>}
      <div className="card">
        <h3>Baseline vs XGBoost on the test window</h3>
        <DataTable
          rows={data.comparison_test}
          columns={[
            { key: "Model", label: "Model" },
            { key: "MAE", label: "MAE", type: "num" },
            { key: "RMSE", label: "RMSE", type: "num" },
            { key: "MAPE", label: "MAPE", type: "pct" },
            { key: "WAPE", label: "WAPE", type: "pct" },
          ]}
        />
        <p className="note">MAPE: {data.metric_explanations.MAPE} WAPE: {data.metric_explanations.WAPE}</p>
      </div>
      <div className="card">
        <h3>What the model relied on most</h3>
        <div style={{ height: 360 }}>
          <ResponsiveContainer>
            <BarChart
              data={data.feature_importance.slice(0, 12).map((row) => ({
                ...row,
                label: featureLabel(row.feature),
              }))}
              layout="vertical"
              margin={{ left: 8, right: 16 }}
            >
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#5a6b78" }} />
              <YAxis type="category" dataKey="label" width={210} tick={{ fontSize: 11, fill: "#5a6b78" }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: "rgba(13, 44, 68, 0.04)" }} formatter={(value) => [Number(value).toLocaleString("en-IN"), "Importance (gain)"]} />
              <Bar dataKey="gain" fill="#1a4a6e" name="Importance (gain)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="note">These names describe the sales history the model used. Higher gain means the feature helped more with the forecast. It does not mean the feature caused sales to change.</p>
      </div>
      <div className="card">
        <h3>Ask a grounded business question</h3>
        <p className="note">The evidence-based summary follows the question you ask. Numbers come only from calculated backend results.</p>
        <div className="prompt-row">
          <input value={question} onChange={(e) => setQuestion(e.target.value)} />
          <button className="btn" onClick={ask} disabled={busy}>{busy ? "Working…" : "Generate insight"}</button>
        </div>
        <div className="chip-row" style={{ marginTop: 12 }}>
          {[
            "How does XGBoost compare with the baselines on the December holdout?",
            "Which categories perform best?",
            "Which cities lead revenue?",
            "Which categories need inventory attention?",
          ].map((sample) => (
            <button key={sample} type="button" className="chip chip-btn" onClick={() => setQuestion(sample)}>
              {sample}
            </button>
          ))}
        </div>
        {insight ? (
          <div style={{ marginTop: 16 }}>
            <InsightCard title={insight.grounded ? "Validated explanation" : "Response"}>
              {insight.answer}
            </InsightCard>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function fmt(value) {
  return Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
