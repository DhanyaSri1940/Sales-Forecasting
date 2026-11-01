# Indian FMCG Sales Intelligence & Forecasting Platform

Professional sales forecasting and retail analytics application for a **simulated/educational** Indian FMCG retailer covering calendar year **2024**.

The primary model is **XGBoost regression** on **daily category revenue**. A React frontend and FastAPI backend present historical performance, recursive forecasts, and LangGraph-orchestrated explanations that are grounded in calculated metrics.

## Problem Statement

FMCG operators need a single view of what already happened, how sales are trending, and what is likely next. Transaction-level invoices cannot be treated as a time series. They must be validated, aggregated, forecasted without leakage, and compared honestly with simple baselines.

## Business Objective

Help a business user answer:

1. What happened to sales?
2. How are sales trending?
3. What is likely to happen next?
4. Which categories, cities, brands, and channels perform best?
5. Which categories have strong or weak margins?
6. How well does XGBoost perform versus naive baselines?
7. Which categories have thinner stock cover relative to expected demand?

## Dataset Description

| Item | Value |
| --- | --- |
| File | `data/raw/indian_fmcg_retail_sales_2024.csv` (copy of the supplied original; not modified) |
| Rows | 100,000 invoices |
| Calendar | 2024-01-01 through 2024-12-30 (365 days) |
| Geography | Ahmedabad, Bengaluru, Chennai, Delhi, Hyderabad, Kolkata, Mumbai, Pune |
| Categories | Beverages, Dairy, Fruits, Grocery, Home Care, Personal Care, Snacks, Vegetables |
| Nature | Simulated / educational Indian FMCG retail dataset |

Columns used exactly as supplied: `Invoice_ID`, `Invoice_Date`, `City`, `Store_Format`, `Category`, `Brand`, `Channel`, `Payment_Mode`, `Units`, `Cost_Price`, `Selling_Price`, `Revenue`, `Cost`, `Margin`, `Margin_%`, `Stock_On_Hand`, `Reorder_Level`, `Lead_Time_Days`, `Customer_Age`, `Customer_Gender`, `Loyalty_Flag`.

## Dataset Limitations

Explicitly **not** in the file and **not fabricated**:

- Discount, advertising spend, marketing spend
- Weather, holidays, customer traffic
- Returns / wastage
- Multi-year history

Customer age is missing for 40,081 invoices and is **never imputed**. Missing gender is reported as unavailable.

This is **not** proprietary company data.

## Technology Stack

- Frontend: React (Vite), Recharts
- Backend: Python FastAPI
- ML: XGBoost (`reg:squarederror`), scikit-learn `TimeSeriesSplit`
- Data: pandas, NumPy
- Orchestration: LangGraph (retrieve → analyze → validate → generate)
- Model storage: XGBoost JSON (`models/xgboost_sales_model.json`)

## System Architecture

```
User → React UI → REST /api → FastAPI
                              ├─ Analytics (pandas)
                              ├─ Forecasting (loaded XGBoost, no retraining)
                              └─ LangGraph insight graph (uses validated metrics only)
```

Changing a dashboard filter does **not** retrain the model.

## Frontend Architecture

Four pages plus Inventory & Demand: Executive Dashboard, Sales Forecast, Sales Analytics, Inventory & Demand, Model Performance. Shared components handle KPIs, charts, tables, loading skeletons, and errors.

## Backend Architecture

Routers under `backend/app/routes/` expose dashboard, forecast, analytics, and model endpoints. Services load cached processed data and the trained booster.

## ML Pipeline

RAW DATA → validation → cleaning (documented, no silent deletes) → Date × Category aggregation → EDA/KPIs → calendar + lag + rolling features → leakage audit → chronological split → TimeSeriesSplit tuning on train only → early stopping on November validation → one-time December test → recursive 7/14/30-day forecast.

## AI / LangGraph Architecture

`retrieve` loads KPIs, rankings, and test metrics from the backend. `analyze` extracts a compact evidence dict. `validate` flags requests for fields that are not in the dataset. `generate` writes a narrative from those numbers (optional LLM only if `OPENAI_API_KEY` is set; otherwise a deterministic template). Unsupported claims are blocked.

## Data Processing

- Duplicate `Invoice_ID` values (62 extra occurrences) are **distinct transactions** (different date/city/category). All rows are kept. `Invoice_ID` is not a unique key.
- No identical full-row duplicates.
- No negative units, prices, revenue, stock, or lead times.
- High-revenue invoices were reviewed and **not** removed (max invoice revenue is consistent with 1–5 units).
- `Date` is the calendar day of `Invoice_Date`.

See `data/processed/cleaning_log.json`.

## Forecasting Grain

**Selected: Date × Category, target = daily revenue.**

| Grain | Cells | Missing | Min invoices / cell |
| --- | --- | --- | --- |
| Date × Category | 2,920 | 0 | 16 |
| Date × City × Category | 23,032 | 328 | 1 |

Date × Category is complete and stable. City / brand / channel / store-format **forecast views** are top-down allocations of category forecasts using trailing 30-day revenue shares. That allocation is labeled as an **assumption** in the API and UI.

## Feature Engineering

Known in advance: year, month, quarter, day, day of week, week of year, weekend, month start/end, category.

Safe historical: `lag_1`, `lag_7`, `lag_14`, `lag_30`, rolling mean/std/min/max on **shifted** revenue (`shift(1).rolling(...)`).

**Not used** (leakage or not known at prediction time): same-day revenue, units, margin, prices, customer attributes, invoice-level stock.

## Time-Series Validation

The file is a single year. Additional years are **not invented**.

- Train: through 2024-10-31
- Validation (early stopping + inspection): 2024-11-01 to 2024-11-30
- Test (once): 2024-12-01 to 2024-12-30
- Hyperparameters: `TimeSeriesSplit` (3 folds) **inside the training window only**

## XGBoost

`objective=reg:squarederror`. Conservative depth, `min_child_weight`, subsample, column sample, L1/L2, and early stopping on validation MAE. Test data is never used for stopping or tuning.

## Evaluation Metrics

Reported as **MAE, RMSE, MAPE, WAPE** — not “accuracy”. Compared with naive previous-day, 7-day moving average, and 7-day seasonal naive on the same test cells.

## How to Run

```bash
python -m pip install -r backend/requirements.txt
python -m src.train
python -m pytest
python -m uvicorn backend.app.main:app --reload --app-dir .

cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs: `http://127.0.0.1:8000/docs`.

Optional: set `OPENAI_API_KEY` if you want the insight node to call an LLM. Numbers still come from the backend.

## API Documentation

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness |
| GET | `/api/dashboard` | KPIs, trends, rankings |
| GET | `/api/forecast` | `horizon=7\|14\|30` plus optional city/category/brand/channel/store_format |
| GET | `/api/analytics/categories` (also cities, brands, channels, store-formats, payment-modes, loyalty, daily, monthly) | Contribution tables |
| GET | `/api/inventory/risk` | Category stock-cover vs 30-day forecast ranking |
| GET | `/api/model/performance` | Train/valid/test + baselines |
| GET | `/api/model/features` | Gain importance |
| POST | `/api/insights` | LangGraph grounded narrative |

## UI Screens

1. Executive dashboard — year KPIs, trend, holdout actual vs forecast, category/city, inventory vs demand
2. Sales forecast — 7/14/30-day recursive forecast and CSV download
3. Sales analytics — interactive mix charts
4. Inventory & demand — days of stock vs 30-day forecast (relative ranking, not an observed stockout)
5. Model performance — error metrics, importance, insight box

## Limitations

- One simulated year; generalization beyond 2024 is untested.
- Recursive multi-step forecasts can accumulate error; no prediction intervals (none were estimated).
- Filter-level forecasts other than category are allocated, not independently modeled.
- Inventory status is a relative ranking across categories. Stock on hand is never zero in this file, so a stockout is not claimed.
- No promotional or weather drivers.

## Future Improvements

- Independent models at Date × City × Category if more history is available
- Quantile regression for intervals
- Legitimate holiday calendars joined on date
- Hierarchical reconciliation (MinT) instead of trailing-share allocation

## Project Structure

See the repository tree: `src/` (deterministic pipeline), `backend/` (API + LangGraph), `frontend/` (React), `notebooks/`, `models/`, `data/`, `outputs/`, `tests/`.
