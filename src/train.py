"""Train XGBoost on a chronological split with time-series validation.

Never shuffles time. Never uses the test window for early stopping or tuning.
"""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

from src.aggregation import aggregate_forecast_panel, grain_coverage_report, save_panel
from src.baseline import baseline_predictions
from src.business_analysis import build_analytics_payload, inventory_risk
from src.data_loader import load_raw
from src.evaluate import regression_metrics
from src.feature_engineering import (
    LEAKAGE_AUDIT,
    assert_no_future_leakage,
    model_feature_columns,
    prepare_model_frame,
)
from src.forecast import recursive_forecast
from src.preprocessing import clean_transactions, inspect_raw
from src.utils import (
    DATA_PROCESSED,
    FORECASTS_DIR,
    METRICS_DIR,
    MODELS_DIR,
    TARGET_COL,
    TRAIN_END,
    VALID_END,
    ensure_dirs,
    write_json,
)


def _encode_category(series: pd.Series, encoder: dict[str, int] | None = None) -> tuple[pd.Series, dict[str, int]]:
    if encoder is None:
        cats = sorted(series.unique().tolist())
        encoder = {c: i for i, c in enumerate(cats)}
    return series.map(encoder).astype(int), encoder


def _split_masks(dates: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    train = dates <= TRAIN_END
    valid = (dates > TRAIN_END) & (dates <= VALID_END)
    test = dates > VALID_END
    return train, valid, test


def _x_y(df: pd.DataFrame, encoder: dict[str, int]) -> tuple[pd.DataFrame, np.ndarray]:
    frame = df.copy()
    frame["Category"], _ = _encode_category(frame["Category"], encoder)
    cols = model_feature_columns()
    return frame[cols], frame[TARGET_COL].to_numpy(dtype=float)


def _fit_booster(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
    params: dict[str, Any],
    num_boost_round: int = 800,
    early_stopping_rounds: int = 40,
) -> xgb.Booster:
    dtrain = xgb.DMatrix(x_train, label=y_train, feature_names=list(x_train.columns))
    dvalid = xgb.DMatrix(x_valid, label=y_valid, feature_names=list(x_valid.columns))
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=num_boost_round,
        evals=[(dtrain, "train"), (dvalid, "valid")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False,
    )
    return booster


def _predict(booster: xgb.Booster, x: pd.DataFrame) -> np.ndarray:
    dmat = xgb.DMatrix(x, feature_names=list(x.columns))
    return booster.predict(dmat)


def _tune(train_df: pd.DataFrame, encoder: dict[str, int]) -> dict[str, Any]:
    """Small grid + TimeSeriesSplit on the training window only."""
    grid = {
        "max_depth": [3, 4],
        "learning_rate": [0.05, 0.1],
        "min_child_weight": [5],
        "subsample": [0.8],
        "colsample_bytree": [0.8],
        "reg_alpha": [0.1],
        "reg_lambda": [1.0, 5.0],
    }
    keys = list(grid.keys())
    combos = list(itertools.product(*[grid[k] for k in keys]))
    dates = np.sort(train_df["Date"].unique())
    tscv = TimeSeriesSplit(n_splits=3)
    ranked: list[dict[str, Any]] = []

    for combo in combos:
        cand = dict(zip(keys, combo))
        params = {
            "objective": "reg:squarederror",
            "eval_metric": "mae",
            "tree_method": "hist",
            "max_depth": cand["max_depth"],
            "eta": cand["learning_rate"],
            "min_child_weight": cand["min_child_weight"],
            "subsample": cand["subsample"],
            "colsample_bytree": cand["colsample_bytree"],
            "alpha": cand["reg_alpha"],
            "lambda": cand["reg_lambda"],
            "seed": 42,
        }
        fold_mae: list[float] = []
        for fold_train_idx, fold_valid_idx in tscv.split(dates):
            train_dates = set(dates[fold_train_idx])
            valid_dates = set(dates[fold_valid_idx])
            tr = train_df[train_df["Date"].isin(train_dates)]
            va = train_df[train_df["Date"].isin(valid_dates)]
            x_tr, y_tr = _x_y(tr, encoder)
            x_va, y_va = _x_y(va, encoder)
            booster = _fit_booster(x_tr, y_tr, x_va, y_va, params, num_boost_round=400, early_stopping_rounds=30)
            pred = _predict(booster, x_va)
            fold_mae.append(float(np.mean(np.abs(y_va - pred))))
        ranked.append({"params": cand, "cv_mae": float(np.mean(fold_mae))})

    ranked.sort(key=lambda r: r["cv_mae"])
    return {"best": ranked[0], "all": ranked}


def _category_baselines(panel: pd.DataFrame, test_start: pd.Timestamp, test_end: pd.Timestamp) -> dict[str, Any]:
    """Evaluate baselines on the same Date × Category test cells as XGBoost."""
    names = ["Naive previous-period", "Moving average (7-day)", "Seasonal naive (7-day)"]
    collected = {n: {"y": [], "p": []} for n in names}
    for cat, g in panel.groupby("Category"):
        g = g.sort_values("Date").set_index("Date")
        eval_index = g.index[(g.index > VALID_END) & (g.index <= test_end)]
        preds = baseline_predictions(g[TARGET_COL], eval_index)
        y = g.loc[eval_index, TARGET_COL].to_numpy()
        for n in names:
            collected[n]["y"].append(y)
            collected[n]["p"].append(preds[n])
    rows = []
    for n in names:
        y = np.concatenate(collected[n]["y"])
        p = np.concatenate(collected[n]["p"])
        mask = np.isfinite(p)
        rows.append({"Model": n, **regression_metrics(y[mask], p[mask])})
    return {"table": rows}


def train() -> dict[str, Any]:
    ensure_dirs()
    raw = load_raw()
    inspection = inspect_raw(raw)
    write_json(DATA_PROCESSED / "data_inspection.json", inspection)

    tx, cleaning_log = clean_transactions(raw)
    tx.to_pickle(DATA_PROCESSED / "transactions.pkl")

    coverage = grain_coverage_report(tx)
    write_json(DATA_PROCESSED / "grain_coverage.json", coverage)

    panel = aggregate_forecast_panel(tx)
    save_panel(panel)

    featured = prepare_model_frame(panel)
    assert_no_future_leakage(featured)

    train_mask, valid_mask, test_mask = _split_masks(featured["Date"])
    train_df = featured.loc[train_mask].copy()
    valid_df = featured.loc[valid_mask].copy()
    test_df = featured.loc[test_mask].copy()

    _, encoder = _encode_category(featured["Category"])
    x_train, y_train = _x_y(train_df, encoder)
    x_valid, y_valid = _x_y(valid_df, encoder)
    x_test, y_test = _x_y(test_df, encoder)

    tuning = _tune(train_df, encoder)
    best = tuning["best"]["params"]
    final_params = {
        "objective": "reg:squarederror",
        "eval_metric": "mae",
        "tree_method": "hist",
        "max_depth": best["max_depth"],
        "eta": best["learning_rate"],
        "min_child_weight": best["min_child_weight"],
        "subsample": best["subsample"],
        "colsample_bytree": best["colsample_bytree"],
        "alpha": best["reg_alpha"],
        "lambda": best["reg_lambda"],
        "seed": 42,
    }

    booster = _fit_booster(x_train, y_train, x_valid, y_valid, final_params)
    train_pred = _predict(booster, x_train)
    valid_pred = _predict(booster, x_valid)
    test_pred = _predict(booster, x_test)

    train_metrics = regression_metrics(y_train, train_pred)
    valid_metrics = regression_metrics(y_valid, valid_pred)
    test_metrics = regression_metrics(y_test, test_pred)

    baseline = _category_baselines(panel, TRAIN_END, VALID_END.replace(month=12, day=30))
    xgb_row = {"Model": "XGBoost", **test_metrics}
    comparison = baseline["table"] + [xgb_row]

    importance = booster.get_score(importance_type="gain")
    imp_rows = sorted(
        [{"feature": k, "gain": float(v)} for k, v in importance.items()],
        key=lambda r: r["gain"],
        reverse=True,
    )

    model_path = MODELS_DIR / "xgboost_sales_model.json"
    booster.save_model(model_path)

    test_out = test_df[["Date", "Category", TARGET_COL]].copy()
    test_out["Predicted_Revenue"] = test_pred
    test_out.to_csv(FORECASTS_DIR / "test_predictions.csv", index=False)

    history = panel[panel["Date"] <= panel["Date"].max()][["Date", "Category", TARGET_COL]]
    future = recursive_forecast(history, booster, encoder, horizon=30)
    future.to_csv(FORECASTS_DIR / "future_forecast_30d.csv", index=False)
    inventory_risk(tx, future).to_csv(DATA_PROCESSED / "inventory_risk.csv", index=False)

    analytics = build_analytics_payload(tx)

    overfitting_note = None
    if valid_metrics["MAE"] > 1.35 * train_metrics["MAE"]:
        overfitting_note = (
            "Validation MAE is substantially higher than training MAE, which may indicate overfitting. "
            "The selected hyperparameters remain conservative (shallow trees, min_child_weight, subsample, "
            "column sampling, L1/L2 regularization, and early stopping on the validation window)."
        )

    hyperparameter_notes = {
        "max_depth": "Limits tree depth; lower values reduce overfitting on noisy daily series.",
        "learning_rate": "Shrinks each tree's contribution; lower values need more trees but generalize more smoothly.",
        "min_child_weight": "Requires more evidence before a split; reduces fits to tiny leaf samples.",
        "subsample": "Row sampling per tree; reduces variance.",
        "colsample_bytree": "Feature sampling per tree; reduces reliance on a few lags.",
        "reg_alpha": "L1 regularization on leaf weights.",
        "reg_lambda": "L2 regularization on leaf weights.",
        "early_stopping": (
            "Stops boosting when validation MAE stops improving so extra trees are not added after "
            "the model starts fitting training noise. The test window is never used for stopping."
        ),
    }

    split_info = {
        "dataset_date_range": [str(panel["Date"].min().date()), str(panel["Date"].max().date())],
        "train": f"through {TRAIN_END.date()}",
        "validation": f"{(TRAIN_END + pd.Timedelta(days=1)).date()} through {VALID_END.date()}",
        "test": f"{(VALID_END + pd.Timedelta(days=1)).date()} through {panel['Date'].max().date()}",
        "limitation": (
            "The supplied file covers a single simulated year (2024). A multi-year holdout is not available "
            "and is not fabricated. Chronological train/validation/test within 2024 is used instead, plus "
            "TimeSeriesSplit on the training window."
        ),
        "train_rows": int(len(train_df)),
        "valid_rows": int(len(valid_df)),
        "test_rows": int(len(test_df)),
        "best_iteration": int(getattr(booster, "best_iteration", 0) or 0),
    }

    metrics_payload = {
        "split": split_info,
        "xgboost_train": train_metrics,
        "xgboost_validation": valid_metrics,
        "xgboost_test": test_metrics,
        "comparison_test": comparison,
        "feature_importance": imp_rows,
        "best_hyperparameters": best,
        "cv_best_mae": tuning["best"]["cv_mae"],
        "hyperparameter_notes": hyperparameter_notes,
        "overfitting_note": overfitting_note,
        "leakage_audit_summary": {
            "used_in_model": LEAKAGE_AUDIT["used_in_model"],
            "excluded": list(LEAKAGE_AUDIT["excluded_and_why"].keys()),
        },
        "recursive_forecast_note": (
            "Multi-step forecasts are recursive: each predicted day is fed into subsequent lag and rolling "
            "features. Error can accumulate over longer horizons. No prediction intervals are shown because "
            "none were estimated."
        ),
    }
    write_json(METRICS_DIR / "metrics.json", metrics_payload)
    write_json(
        MODELS_DIR / "feature_spec.json",
        {
            "feature_columns": model_feature_columns(),
            "category_encoder": encoder,
            "target": TARGET_COL,
            "grain": ["Date", "Category"],
            "model_path": str(model_path),
        },
    )

    pd.DataFrame(imp_rows).to_csv(METRICS_DIR / "feature_importance.csv", index=False)
    pd.DataFrame(comparison).to_csv(METRICS_DIR / "model_comparison.csv", index=False)

    return {
        "inspection_rows": inspection["row_count"],
        "cleaning": cleaning_log["rows_out"],
        "metrics": metrics_payload,
        "analytics_kpis": analytics["kpis"],
        "model_path": str(model_path),
    }


if __name__ == "__main__":
    result = train()
    print("Trained XGBoost. Test metrics:", result["metrics"]["xgboost_test"])
    print("Comparison:", result["metrics"]["comparison_test"])
    print("Model:", result["model_path"])
