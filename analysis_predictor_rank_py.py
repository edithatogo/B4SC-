import pandas as pd
import numpy as np
import os

# Attempt to import shared functions or load shared data if Data_and_Functions.R was fully converted
# For now, we'll redefine necessary loading or use placeholders if specific processing is needed here.

def load_csv_data_ar(filename: str, **kwargs) -> pd.DataFrame: # ar for analysis_rank
    """Helper function to load CSV data with error handling for this script."""
    print(f"AR_PY: Loading {filename}...")
    try:
        return pd.read_csv(filename, **kwargs)
    except FileNotFoundError:
        print(f"AR_PY: Warning: File {filename} not found. Returning empty DataFrame.")
        return pd.DataFrame()

def calculate_rr_ci(df: pd.DataFrame, ref_df: pd.DataFrame, id_cols: list,
                    incomplete_cols: list = ['vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']) -> pd.DataFrame:
    """
    Calculates Relative Risks (RR) and Confidence Intervals (CI).
    df: DataFrame with predictor levels.
    ref_df: DataFrame with reference level data for each predictor ('var').
            Expected columns in ref_df: 'var' + id_cols (if any for matching scope, e.g. DHB)
                                       'ref_total', 'ref_vht', 'ref_nurse', 'ref_sdqt'.
    id_cols: Columns to merge ref_df on, besides 'var'. E.g., ['DHB2015_name']. For national, it's empty.
    """
    if df.empty or ref_df.empty:
        return pd.DataFrame()

    merge_cols = ['var'] + id_cols
    processed_df = pd.merge(df, ref_df, on=merge_cols, how="left")

    for col_type in ['vht', 'nurse', 'sdqt']:
        incomplete_col = f'{col_type}_incomplete'
        ref_incomplete_col = f'ref_{col_type}'
        rr_col = f'rr_{col_type}'
        ci_col = f'ci_{col_type}'
        ci_ll_col = f'{col_type}_ci_ll'
        ci_ul_col = f'{col_type}_ci_ul'

        if incomplete_col not in processed_df.columns or \
           ref_incomplete_col not in ref_df.columns or \
           'total' not in processed_df.columns or \
           'ref_total' not in ref_df.columns: # ref_total would be in ref_df and merged
            print(f"AR_PY: Warning: Missing required columns for RR/CI calculation for {col_type}.")
            processed_df[rr_col] = np.nan
            processed_df[ci_ll_col] = np.nan
            processed_df[ci_ul_col] = np.nan
            continue

        # Ensure numeric types
        for c in [incomplete_col, 'total', ref_incomplete_col, 'ref_total']:
            processed_df[c] = pd.to_numeric(processed_df[c], errors='coerce')

        # Calculate rates, handling potential division by zero by resulting in NaN/inf
        rate_group = processed_df[incomplete_col] / processed_df['total']
        rate_ref_group = processed_df[ref_incomplete_col] / processed_df['ref_total']

        # Calculate RR: (rate_group / rate_ref_group)
        # Only calculate for non-reference levels (where V3 or ref_level_indicator is "")
        # The input df should already be filtered for non-reference levels if this is desired.
        processed_df[rr_col] = np.where(rate_ref_group > 0, rate_group / rate_ref_group, np.nan)

        # Calculate CI
        # term1 = (((n1-x1)/x1)/n1) where x1=incomplete, n1=total
        term1_x1 = processed_df[incomplete_col]
        term1_n1 = processed_df['total']
        term1 = np.where((term1_x1 > 0) & (term1_n1 > 0), (((term1_n1 - term1_x1) / term1_x1) / term1_n1), np.nan)

        # term2 = (((n2-x2)/x2)/n2) where x2=ref_incomplete, n2=ref_total
        term2_x2 = processed_df[ref_incomplete_col]
        term2_n2 = processed_df['ref_total']
        term2 = np.where((term2_x2 > 0) & (term2_n2 > 0), (((term2_n2 - term2_x2) / term2_x2) / term2_n2), np.nan)

        se_val_squared = term1 + term2 # Addition handles NaNs correctly (result is NaN if any part is NaN)
        processed_df[ci_col] = np.where(se_val_squared > 0, 1.96 * np.sqrt(se_val_squared), np.nan)

        log_rr = np.where(processed_df[rr_col] > 0, np.log(processed_df[rr_col]), np.nan)

        processed_df[ci_ll_col] = np.exp(log_rr - processed_df[ci_col])
        processed_df[ci_ul_col] = np.exp(log_rr + processed_df[ci_col])

    return processed_df


def rank_predictors(df: pd.DataFrame, rr_col: str, group_col: str = 'var_label', num_top: int = 10) -> pd.DataFrame:
    """Ranks predictors based on RR for a given module."""
    if df.empty or rr_col not in df.columns or group_col not in df.columns:
        return pd.DataFrame()

    # Ensure rr_col is numeric for max() and sorting
    df[rr_col] = pd.to_numeric(df[rr_col], errors='coerce')

    ranked_df = df[df[rr_col].notna()].copy()
    # Within each predictor variable (var_label), find the level with the max RR
    # This replicates: group_by(var_label) %>% filter(rr_vht == max(rr_vht))
    ranked_df = ranked_df.loc[ranked_df.groupby(group_col, dropna=False)[rr_col].idxmax()]
    ranked_df = ranked_df.sort_values(by=[rr_col, group_col, 'level_label'], ascending=[False, True, True])

    return ranked_df.head(num_top)


def main_predictor_ranking(output_dir="."):
    """Main function to perform predictor ranking analysis."""
    os.makedirs(output_dir, exist_ok=True)

    # --- Load common data ---
    var_labs_df = load_csv_data_ar("list of var levels.csv", header=None, names=['V1', 'V2', 'V3', 'V4', 'V5'])
    if var_labs_df.empty:
        print("AR_PY: Critical error: list of var levels.csv not found. Cannot proceed.")
        return

    # --- National Level Analysis ---
    print("\nAR_PY: --- Starting National Level Analysis ---")
    national_incomplete_df = load_csv_data_ar("national_incomplete.csv")
    if not national_incomplete_df.empty:
        national_incomplete_df = pd.merge(national_incomplete_df, var_labs_df,
                                          left_on=["var", "level"], right_on=["V1", "V2"], how="left")
        national_incomplete_df.rename(columns={"V4": "var_label", "V5": "level_label", "V3": "ref_level_indicator"}, inplace=True)

        # Clean labels
        national_incomplete_df['var_label'] = national_incomplete_df['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False)
        national_incomplete_df['level_label'] = national_incomplete_df['level_label'].str.replace("Tertiary below Bachelor", "Tertiary", regex=False)
        national_incomplete_df['level_label'] = national_incomplete_df['level_label'].str.replace("No qualifications", "No quals", regex=False)

        # Prepare reference data for national level
        national_ref_values = national_incomplete_df[national_incomplete_df['ref_level_indicator'] == "ref"].copy()
        national_ref_values = national_ref_values[['var', 'total', 'vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']]
        national_ref_values.rename(columns={
            'total': 'ref_total', 'vht_incomplete': 'ref_vht',
            'nurse_incomplete': 'ref_nurse', 'sdqt_incomplete': 'ref_sdqt'
        }, inplace=True)

        # Filter for non-reference levels before calculating RR/CI
        national_analysis_data = national_incomplete_df[national_incomplete_df['ref_level_indicator'] == ""].copy()
        national_incomplete_ref_ci_df = calculate_rr_ci(national_analysis_data, national_ref_values, id_cols=[])

        # Exclude specific groups
        national_incomplete_ref_ci_df = national_incomplete_ref_ci_df[
            ~national_incomplete_ref_ci_df['var'].isin(["bw_grp", "los_days_grp"])
        ].copy()

        # Rank predictors nationally
        top10_pred_vht_nation = rank_predictors(national_incomplete_ref_ci_df, 'rr_vht')
        print("\nAR_PY: Top 10 VHT Predictors (National):\n", top10_pred_vht_nation[['var_label', 'level_label', 'rr_vht']])

        top10_pred_nurse_nation = rank_predictors(national_incomplete_ref_ci_df, 'rr_nurse')
        print("\nAR_PY: Top 10 Nurse Predictors (National):\n", top10_pred_nurse_nation[['var_label', 'level_label', 'rr_nurse']])

        top10_pred_sdqt_nation = rank_predictors(national_incomplete_ref_ci_df, 'rr_sdqt')
        print("\nAR_PY: Top 10 SDQT Predictors (National):\n", top10_pred_sdqt_nation[['var_label', 'level_label', 'rr_sdqt']])

        # Categorized national analysis (Family Socioeconomic, Family & Child, Health System)
        # This requires 'batch' column which was defined in Data_and_Functions.R's all_plot_data_df
        # If we need it here, we'd replicate the batch assignment logic.
        # For now, this part is conceptual as 'batch' is not created here.
        print("\nAR_PY: (Conceptual) National predictor ranking by category would occur here if 'batch' column was available.")

    else:
        print("AR_PY: National incomplete data not found. Skipping national analysis.")

    # --- DHB Level Analysis ---
    print("\nAR_PY: --- Starting DHB Level Analysis ---")
    # The R script uses 'dhb_incomplete_ref_ci' which is assumed to be pre-calculated
    # This would be the output of RR/CI calculation on 'dhb_fulldata.csv'
    # For Python, this means data_and_functions_py.py should produce it, or we load dhb_fulldata.csv and calc here.

    # Let's assume 'all_plot_data_df' from data_and_functions_py.py is the equivalent of R's 'dhb_incomplete_ref_ci'
    # And it's loaded or passed. For now, we'll try to load it if Data_and_Functions.py saved it.
    # Or, we recalculate it here from dhb_fulldata.csv
    dhb_incomplete_df = load_csv_data_ar("dhb_fulldata.csv") # This is the raw summary from SAS
    dhb_incomplete_ref_ci_py_df = pd.DataFrame()

    if not dhb_incomplete_df.empty:
        dhb_incomplete_df = pd.merge(dhb_incomplete_df, var_labs_df,
                                     left_on=["var", "level"], right_on=["V1", "V2"], how="left")
        dhb_incomplete_df.rename(columns={"V4": "var_label", "V5": "level_label", "V3": "ref_level_indicator"}, inplace=True)
        dhb_incomplete_df['var_label'] = dhb_incomplete_df['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False) # etc.

        dhb_ref_values = dhb_incomplete_df[dhb_incomplete_df['ref_level_indicator'] == "ref"].copy()
        dhb_ref_values = dhb_ref_values[['var', 'DHB2015_name', 'total', 'vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']]
        dhb_ref_values.rename(columns={
            'total': 'ref_total', 'vht_incomplete': 'ref_vht',
            'nurse_incomplete': 'ref_nurse', 'sdqt_incomplete': 'ref_sdqt'
        }, inplace=True)

        dhb_analysis_data = dhb_incomplete_df[dhb_incomplete_df['ref_level_indicator'] == ""].copy()
        dhb_incomplete_ref_ci_py_df = calculate_rr_ci(dhb_analysis_data, dhb_ref_values, id_cols=['DHB2015_name'])
        dhb_incomplete_ref_ci_py_df = dhb_incomplete_ref_ci_py_df[
            ~dhb_incomplete_ref_ci_py_df['var'].isin(["bw_grp", "los_days_grp"])
        ].copy()
    else:
        print("AR_PY: dhb_fulldata.csv not found. Skipping DHB analysis.")

    if not dhb_incomplete_ref_ci_py_df.empty:
        dhb_names = dhb_incomplete_ref_ci_py_df['DHB2015_name'].unique()

        all_top10_vht_dhb = []
        for dhb in dhb_names:
            if pd.isna(dhb): continue
            top10 = rank_predictors(dhb_incomplete_ref_ci_py_df[dhb_incomplete_ref_ci_py_df['DHB2015_name'] == dhb], 'rr_vht')
            top10['DHB2015_name'] = dhb # Add DHB name for context when saving list
            all_top10_vht_dhb.append(top10)
        if all_top10_vht_dhb:
            pd.concat(all_top10_vht_dhb).to_csv(os.path.join(output_dir, "top10_vht_dhb.csv"), index=False)
            print("AR_PY: top10_vht_dhb.csv generated.")
            top10_vht_freq_list = pd.concat(all_top10_vht_dhb)['var_label'].value_counts().nlargest(10)
            print("\nAR_PY: Most frequent Top 10 VHT predictors across DHBs:\n", top10_vht_freq_list)

        all_top10_nurse_dhb = []
        for dhb in dhb_names:
            if pd.isna(dhb): continue
            top10 = rank_predictors(dhb_incomplete_ref_ci_py_df[dhb_incomplete_ref_ci_py_df['DHB2015_name'] == dhb], 'rr_nurse')
            top10['DHB2015_name'] = dhb
            all_top10_nurse_dhb.append(top10)
        if all_top10_nurse_dhb:
            pd.concat(all_top10_nurse_dhb).to_csv(os.path.join(output_dir, "top10_nurse_dhb.csv"), index=False) # R script names it top10_nurse_freq.csv
            print("AR_PY: top10_nurse_dhb.csv generated.")
            top10_nurse_freq_list = pd.concat(all_top10_nurse_dhb)['var_label'].value_counts().nlargest(10)
            print("\nAR_PY: Most frequent Top 10 Nurse predictors across DHBs:\n", top10_nurse_freq_list)

        all_top10_sdqt_dhb = []
        for dhb in dhb_names:
            if pd.isna(dhb): continue
            top10 = rank_predictors(dhb_incomplete_ref_ci_py_df[dhb_incomplete_ref_ci_py_df['DHB2015_name'] == dhb], 'rr_sdqt')
            top10['DHB2015_name'] = dhb
            all_top10_sdqt_dhb.append(top10)
        if all_top10_sdqt_dhb:
            pd.concat(all_top10_sdqt_dhb).to_csv(os.path.join(output_dir, "top10_sdqt_dhb.csv"), index=False)
            print("AR_PY: top10_sdqt_dhb.csv generated.")
            top10_sdqt_freq_list = pd.concat(all_top10_sdqt_dhb)['var_label'].value_counts().nlargest(10)
            print("\nAR_PY: Most frequent Top 10 SDQT predictors across DHBs:\n", top10_sdqt_freq_list)
    else:
        print("AR_PY: Cannot perform DHB level ranking as dhb_incomplete_ref_ci_py_df is empty.")


    # --- TA/Ward Level Analysis ---
    print("\nAR_PY: --- Starting TA/Ward Level Analysis ---")
    ta_incomplete_df = load_csv_data_ar("grp_taward_final.csv") # R script: grp_taward_final.csv, SAS output: taward_final.csv
    dhb_map_df = load_csv_data_ar("dhb_map.csv")
    ta_incomplete_ref_ci_py_df = pd.DataFrame()

    if not ta_incomplete_df.empty and not var_labs_df.empty and not dhb_map_df.empty:
        # Clean grp_ta_ward_name for merging with dhb_map if needed
        ta_incomplete_df['grp_ta_ward_name'] = ta_incomplete_df['grp_ta_ward_name'].astype(str)
        dhb_map_df['WARD2013_name'] = dhb_map_df['WARD2013_name'].astype(str)
        ta_incomplete_df = pd.merge(ta_incomplete_df, dhb_map_df, left_on="grp_ta_ward_name", right_on="WARD2013_name", how="left")

        ta_incomplete_df = pd.merge(ta_incomplete_df, var_labs_df,
                                    left_on=["var", "level"], right_on=["V1", "V2"], how="left")
        ta_incomplete_df.rename(columns={"V4": "var_label", "V5": "level_label", "V3": "ref_level_indicator"}, inplace=True)
        ta_incomplete_df['var_label'] = ta_incomplete_df['var_label'].str.replace("mother_highest_qual", "Mother highest qual", regex=False) # R script has this replacement

        ta_ref_values = ta_incomplete_df[ta_incomplete_df['ref_level_indicator'] == "ref"].copy()
        ta_ref_values = ta_ref_values[['var', 'grp_ta_ward_name', 'total', 'vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']]
        ta_ref_values.rename(columns={
            'total': 'ref_total', 'vht_incomplete': 'ref_vht',
            'nurse_incomplete': 'ref_nurse', 'sdqt_incomplete': 'ref_sdqt'
        }, inplace=True)

        ta_analysis_data = ta_incomplete_df[ta_incomplete_df['ref_level_indicator'] == ""].copy()
        ta_incomplete_ref_ci_py_df = calculate_rr_ci(ta_analysis_data, ta_ref_values, id_cols=['grp_ta_ward_name'])
        ta_incomplete_ref_ci_py_df = ta_incomplete_ref_ci_py_df[
            ~ta_incomplete_ref_ci_py_df['var'].isin(["bw_grp", "los_days_grp"])
        ].copy()
    else:
        print("AR_PY: Data for TA/Ward analysis not fully loaded. Skipping.")

    if not ta_incomplete_ref_ci_py_df.empty:
        ta_names = ta_incomplete_ref_ci_py_df['grp_ta_ward_name'].unique()
        # Exclude Chatham Islands as in R: ta = unique(ta_incomplete$grp_ta_ward_name)[1:70]
        # This depends on the exact unique values and their order. A more robust filter might be needed.
        # For now, process all valid TAs.

        all_top10_vht_ta = []
        for ta_name in ta_names:
            if pd.isna(ta_name): continue
            top10 = rank_predictors(ta_incomplete_ref_ci_py_df[ta_incomplete_ref_ci_py_df['grp_ta_ward_name'] == ta_name], 'rr_vht')
            top10['grp_ta_ward_name'] = ta_name # Add TA name
            # DHB_name should already be on ta_incomplete_ref_ci_py_df from the merge
            all_top10_vht_ta.append(top10)

        if all_top10_vht_ta:
            pd.concat(all_top10_vht_ta).to_csv(os.path.join(output_dir, "top10_vht_ta.csv"), index=False)
            print("AR_PY: top10_vht_ta.csv generated.")

            top10_vht_ta_df_full = pd.concat(all_top10_vht_ta)

            # Summarize TA top predictors at DHB level
            dhb_ta_summary_list = []
            for dhb_name_val in top10_vht_ta_df_full['DHB_name'].unique():
                if pd.isna(dhb_name_val): continue
                one_dhb_tas_top_preds = top10_vht_ta_df_full[top10_vht_ta_df_full['DHB_name'] == dhb_name_val]
                freq_counts = one_dhb_tas_top_preds['var_label'].value_counts().nlargest(10).reset_index()
                freq_counts.columns = ['var_label', 'Freq']
                freq_counts['DHB_name'] = dhb_name_val
                dhb_ta_summary_list.append(freq_counts)

            if dhb_ta_summary_list:
                 # R saves DHB_ta as a list of dataframes. For CSV, better to concat or save multiple.
                 # For now, concat and add DHB name to distinguish.
                dhb_ta_combined_df = pd.concat(dhb_ta_summary_list)
                dhb_ta_combined_df.to_csv(os.path.join(output_dir, "DHB_ta_summary.csv"), index=False)
                print("AR_PY: DHB_ta_summary.csv (summary of TA top VHT predictors by DHB) generated.")
            else:
                print("AR_PY: No data for DHB_ta_summary.csv.")
    else:
        print("AR_PY: Cannot perform TA/Ward level ranking as ta_incomplete_ref_ci_py_df is empty.")

    # --- Exploratory: Find Max RR values (findmaxrr function in R) ---
    # This used 'allplotdata' in R, which was dhb_incomplete_ref_ci.
    # We use dhb_incomplete_ref_ci_py_df here.
    if not dhb_incomplete_ref_ci_py_df.empty:
        print("\nAR_PY: --- Max RR and CI_UL values by DHB (for plot scaling reference) ---")
        for dhb_name_val in dhb_incomplete_ref_ci_py_df['DHB2015_name'].unique():
            if pd.isna(dhb_name_val): continue
            dhb_data = dhb_incomplete_ref_ci_py_df[dhb_incomplete_ref_ci_py_df['DHB2015_name'] == dhb_name_val]
            print(f"\nAR_PY: DHB: {dhb_name_val}")
            for module in ['vht', 'nurse', 'sdqt']:
                rr_col = f'rr_{module}'
                ci_ul_col = f'{module}_ci_ul'
                if rr_col in dhb_data.columns and ci_ul_col in dhb_data.columns:
                    max_rr = dhb_data[rr_col].max()
                    max_ci_ul = dhb_data[ci_ul_col].max()
                    print(f"AR_PY:   {module.upper()}: Max RR = {max_rr:.2f}, Max CI_UL = {max_ci_ul:.2f}")
    else:
        print("AR_PY: Cannot perform findmaxrr due to empty dhb_incomplete_ref_ci_py_df.")

    print("\nAR_PY: --- Predictor Ranking Analysis Finished ---")


if __name__ == "__main__":
    # Create a dummy output directory for the CSVs
    output_directory = "analysis_rank_outputs_python"
    main_predictor_ranking(output_dir=output_directory)
    print(f"\nAR_PY: Please check the '{os.path.abspath(output_directory)}' directory for output CSV files.")

```
