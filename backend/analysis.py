import pandas as pd
import numpy as np

import pandas as pd
import re

def numeric_converter(raw_data_list):
    # 1. Load the list into a DataFrame
    df = pd.DataFrame(raw_data_list)

    for col in df.columns:
        # We only process columns that are currently strings (objects)
        if df[col].dtype == 'object':
            
            # STEP A: Deep Clean strings (Remove +, -, spaces)
            # We do this to the whole column at once
            clean_col = df[col].astype(str).str.replace(r'[\+\-\s]', '', regex=True)

            # STEP B: Pakistani Phone Logic (The 'Extraordinary' Part) [cite: 2026-02-19]
            # Convert 92... or 0092... to 0...
            clean_col = clean_col.str.replace(r'^92', '0', regex=True)
            clean_col = clean_col.str.replace(r'^0092', '0', regex=True)
            
            # If 10 digits (like 340...), add the missing 0
            mask = (clean_col.str.len() == 10) & (clean_col.str.startswith('3'))
            clean_col.loc[mask] = '0' + clean_col.loc[mask]

            # STEP C: Universal Numeric Check
            # Check if the column is actually numeric after cleaning
            is_numeric = clean_col.str.isnumeric()

            if is_numeric.any():
                # If it's a phone number (11 digits), we keep it as a STRING to preserve the '0'
                # If it's a mark (like 88), we convert to INT for math
                
                # Logic: If max length is 11, it's likely a phone; keep leading zero
                if clean_col.str.len().max() == 11:
                     df[col] = clean_col # Keeps the '0'
                else:
                     df[col] = pd.to_numeric(clean_col, errors='coerce').fillna(0).astype(int)

    return df.to_dict('records')

def perform_universal_math(data_list, col_a, col_b=None):
    """
    One function for all: Sum, Sub, Mean, Std, etc.
    Works on the 'traveling' JSON shards.
    """
    df = pd.DataFrame(data_list)

    # Ensure columns exist and are numeric [cite: 2026-02-15]
    if col_a not in df.columns:
        return {"error": f"Column {col_a} missing"}

    # Basic Statistics on primary column [cite: 2026-02-19]
    results = {
        "mean": float(np.mean(df[col_a])),
        "std_dev": float(np.std(df[col_a])),
        "sum": float(np.sum(df[col_a])),
        "count": int(len(df))
    }

    # Comparative Math (if a second column is provided) [cite: 2026-02-15]
    if col_b and col_b in df.columns:
        results.update({
            "addition": (df[col_a] + df[col_b]).tolist(),
            "subtraction": (df[col_a] - df[col_b]).tolist(),
            "multiplication": (df[col_a] * df[col_b]).tolist(),
            # Prevent division by zero [cite: 2026-02-15]
            "division": (df[col_a] / df[col_b].replace(0, np.nan)).fillna(0).tolist()
        })

    return results

def prepare_graph_data(data_list, group_col, value_col, agg_type="mean"):
    """
    Groups two quantities (e.g., Marks by Year) for offline graphing.
    """
    df = pd.DataFrame(data_list)

    if group_col not in df.columns or value_col not in df.columns:
        return {}

    # Grouping Logic [cite: 2026-02-19]
    if agg_type == "mean":
        grouped = df.groupby(group_col)[value_col].mean()
    elif agg_type == "sum":
        grouped = df.groupby(group_col)[value_col].sum()
    else:
        grouped = df.groupby(group_col)[value_col].count()

    # Format for JS Charts (Labels and Values) [cite: 2026-01-26]
    return {
        "labels": grouped.index.tolist(),
        "datasets": grouped.values.tolist()
    }

import re

def sanitize_pakistani_phone(phone_val):
    """
    Standardizes Pakistani phone numbers to 11-digit format (03XXXXXXXXX).
    Handles +92, 92, 0092, and missing leading zeros.
    """
    if not phone_val:
        return ""

    # 1. Remove all non-numeric characters (spaces, +, -, brackets) [cite: 2026-02-15]
    clean_num = re.sub(r'\D', '', str(phone_val))

    # 2. Handle International Prefix (92) [cite: 2026-02-19]
    if clean_num.startswith('92'):
        clean_num = '0' + clean_num[2:]
    elif clean_num.startswith('0092'):
        clean_num = '0' + clean_num[4:]

    # 3. Handle missing leading zero (e.g., 340 -> 0340) [cite: 2026-02-19]
    if len(clean_num) == 10 and clean_num.startswith('3'):
        clean_num = '0' + clean_num

    # 4. Final Validation: Return if 11 digits, else keep original for manual search [cite: 2026-02-15]
    if len(clean_num) == 11 and clean_num.startswith('03'):
        return clean_num

    return clean_num # Return as-is if it's a landline or weird format
