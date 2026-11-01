from __future__ import annotations

import pandas as pd
import pytest

from src.data_loader import load_raw
from src.feature_engineering import add_lag_and_rolling_features, assert_no_future_leakage, prepare_model_frame
from src.preprocessing import clean_transactions
from src.aggregation import aggregate_forecast_panel
from src.forecast import recursive_forecast
from src.utils import mape


def test_load_raw_shape_and_columns():
    df = load_raw()
    assert len(df) == 100000
    assert df.shape[1] == 21


def test_cleaning_does_not_drop_rows():
    df = load_raw()
    cleaned, log = clean_transactions(df)
    assert log["rows_removed_total"] == 0
    assert len(cleaned) == 100000
    assert cleaned["Customer_Age"].isna().sum() == 40081


def test_lag_matches_previous_day_and_rolling_excludes_today():
    dates = pd.date_range("2024-01-01", periods=10)
    panel = pd.DataFrame(
        {
            "Date": dates,
            "Category": ["Dairy"] * 10,
            "Revenue": [float(i) for i in range(1, 11)],
        }
    )
    featured = add_lag_and_rolling_features(panel)
    last = featured.iloc[-1]
    assert last["lag_1"] == 9.0
    assert last["rolling_mean_7"] == pytest.approx(6.0)


def test_prepare_model_frame_no_lag_leakage():
    tx, _ = clean_transactions(load_raw())
    panel = aggregate_forecast_panel(tx)
    featured = prepare_model_frame(panel)
    assert_no_future_leakage(featured)
    assert featured["lag_1"].notna().all()


def test_mape_skips_zeros():
    assert mape([0, 10], [1, 12]) == pytest.approx(20.0)


def test_horizon_validation():
    with pytest.raises(ValueError):
        recursive_forecast(
            pd.DataFrame({"Date": pd.to_datetime(["2024-01-01"]), "Category": ["Dairy"], "Revenue": [1.0]}),
            booster=None,
            category_encoder={"Dairy": 0},
            horizon=9,
        )


def test_inventory_ranking_uses_plain_status_labels():
    from src.business_analysis import inventory_risk
    from src.utils import FORECASTS_DIR

    future_path = FORECASTS_DIR / "future_forecast_30d.csv"
    if not future_path.exists():
        return
    tx, _ = clean_transactions(load_raw())
    table = inventory_risk(tx, pd.read_csv(future_path))
    allowed = {"Needs attention", "Watch", "In good shape"}
    assert set(table["status"]).issubset(allowed)
    assert table["status"].nunique() >= 2
    assert (tx["Stock_On_Hand"] == 0).sum() == 0
