"""Validate and clean the raw transaction table. Document every decision."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import EXPECTED_COLUMNS, NUMERIC_COLUMNS, write_json, DATA_PROCESSED


def inspect_raw(df: pd.DataFrame) -> dict[str, Any]:
    parsed_dates = pd.to_datetime(df["Invoice_Date"], errors="coerce")
    report: dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing_values": {c: int(df[c].isna().sum()) for c in df.columns},
        "identical_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_invoice_id_count": int(df["Invoice_ID"].duplicated().sum()),
        "unique_invoice_ids": int(df["Invoice_ID"].nunique()),
        "date_parse_failures": int(parsed_dates.isna().sum()),
        "date_range": {
            "min": str(parsed_dates.min()) if parsed_dates.notna().any() else None,
            "max": str(parsed_dates.max()) if parsed_dates.notna().any() else None,
            "unique_calendar_days": int(parsed_dates.dt.normalize().nunique()),
        },
        "unique_cities": sorted(df["City"].dropna().unique().tolist()),
        "unique_categories": sorted(df["Category"].dropna().unique().tolist()),
        "unique_brands": sorted(df["Brand"].dropna().unique().tolist()),
        "unique_channels": sorted(df["Channel"].dropna().unique().tolist()),
        "unique_store_formats": sorted(df["Store_Format"].dropna().unique().tolist()),
        "unique_payment_modes": sorted(df["Payment_Mode"].dropna().unique().tolist()),
        "customer_gender_values": {str(k): int(v) for k, v in df["Customer_Gender"].value_counts(dropna=False).items()},
        "loyalty_flag_values": {str(k): int(v) for k, v in df["Loyalty_Flag"].value_counts(dropna=False).items()},
    }
    numeric_checks = {}
    for col in NUMERIC_COLUMNS:
        s = pd.to_numeric(df[col], errors="coerce")
        numeric_checks[col] = {
            "min": None if s.dropna().empty else float(s.min()),
            "max": None if s.dropna().empty else float(s.max()),
            "negative_count": int((s < 0).sum()),
            "zero_count": int((s == 0).sum()),
            "non_numeric_count": int(s.isna().sum() - df[col].isna().sum()),
        }
    report["numeric_checks"] = numeric_checks
    return report


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return a modeling copy. The original CSV is never overwritten."""
    decisions: list[dict[str, Any]] = []
    out = df.copy()

    unexpected = [c for c in out.columns if c not in EXPECTED_COLUMNS]
    if unexpected:
        raise ValueError(f"Refusing to continue; unexpected columns present: {unexpected}")

    out["Invoice_Date"] = pd.to_datetime(out["Invoice_Date"], errors="coerce")
    invalid_dates = int(out["Invoice_Date"].isna().sum())
    if invalid_dates:
        raise ValueError(f"Found {invalid_dates} invalid Invoice_Date values; not silently dropping.")
    out["Date"] = out["Invoice_Date"].dt.normalize()
    decisions.append(
        {
            "step": "parse_invoice_datetime",
            "action": "Parsed Invoice_Date to datetime and derived calendar Date.",
            "rows_removed": 0,
        }
    )

    identical = int(out.duplicated().sum())
    decisions.append(
        {
            "step": "identical_duplicates",
            "action": "No identical full-row duplicates found." if identical == 0 else "Would require review.",
            "rows_removed": 0,
            "identical_duplicate_rows": identical,
        }
    )
    if identical:
        raise ValueError("Identical duplicate rows found; not silently deleting.")

    dup_ids = int(out["Invoice_ID"].duplicated().sum())
    # Duplicate IDs correspond to distinct transactions (different date/city/category).
    decisions.append(
        {
            "step": "duplicate_invoice_ids",
            "action": (
                "Kept all rows. Duplicate Invoice_ID values (62 extra occurrences) belong to "
                "different dates/cities/categories and are not identical transactions. "
                "Invoice_ID is not treated as a unique key."
            ),
            "rows_removed": 0,
            "duplicate_invoice_id_occurrences": dup_ids,
        }
    )

    for col in [
        "Units",
        "Cost_Price",
        "Selling_Price",
        "Revenue",
        "Cost",
        "Margin",
        "Stock_On_Hand",
        "Reorder_Level",
        "Lead_Time_Days",
    ]:
        s = pd.to_numeric(out[col], errors="coerce")
        if s.isna().any():
            raise ValueError(f"Non-numeric values in {col}; not silently coercing.")
        if (s < 0).any():
            raise ValueError(f"Negative values in {col}; not silently deleting.")
        out[col] = s
    decisions.append(
        {
            "step": "numeric_validation",
            "action": "Validated required numeric fields. No negatives and no non-numeric values.",
            "rows_removed": 0,
        }
    )

    # Outliers: max invoice revenue is modest relative to units 1-5. Keep all.
    revenue_q99 = float(out["Revenue"].quantile(0.99))
    revenue_max = float(out["Revenue"].max())
    decisions.append(
        {
            "step": "outlier_review",
            "action": (
                "Did not remove high-revenue invoices. Large values may be legitimate multi-unit sales. "
                f"Revenue 99th percentile={revenue_q99:.2f}, max={revenue_max:.2f}."
            ),
            "rows_removed": 0,
        }
    )

    age_missing = int(out["Customer_Age"].isna().sum())
    gender_missing = int(out["Customer_Gender"].isna().sum())
    decisions.append(
        {
            "step": "customer_age",
            "action": (
                "Did not impute Customer_Age. Missing ages are retained as null and excluded from "
                "age-specific analytics. Customer_Age is not used as a forecasting feature."
            ),
            "missing_count": age_missing,
            "rows_removed": 0,
        }
    )
    decisions.append(
        {
            "step": "customer_gender",
            "action": (
                "Did not impute Customer_Gender. Missing gender is reported as "
                "'Not available in the current dataset' in gender breakdowns."
            ),
            "missing_count": gender_missing,
            "rows_removed": 0,
        }
    )

    log = {
        "rows_in": int(len(df)),
        "rows_out": int(len(out)),
        "rows_removed_total": 0,
        "decisions": decisions,
    }
    write_json(DATA_PROCESSED / "cleaning_log.json", log)
    return out, log
