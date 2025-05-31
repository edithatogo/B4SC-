import pandas as pd
import numpy as np
import os # For creating output directory if needed

# --- Helper Function for Loading Main Data ---
def load_combined_b4sc_data(path: str = "PYTHON_b4sc_allyr_FINAL.csv") -> pd.DataFrame:
    """
    Loads the combined B4SC dataset (output of '3. combine_years.py').
    """
    print(f"Loading combined B4SC data from {path}...")
    try:
        df = pd.read_csv(path, low_memory=False)
        # Ensure 'year' is int for some summaries
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64') # Allow pd.NA
        return df
    except FileNotFoundError:
        print(f"ERROR: {path} not found. Please ensure 'combine_years.py' has been run successfully.")
        return pd.DataFrame()

# --- Helper Function for Loading Area Concordance ---
def load_annual_areas_2018(path: str = "Annual Areas 2018.csv") -> pd.DataFrame:
    print(f"Loading Annual Areas 2018 from {path} for Local Board mapping...")
    try:
        df = pd.read_csv(path, low_memory=False)
        # Rename for consistency if needed, e.g., MB2018_code to mb2018_code
        df.rename(columns=lambda c: c.lower(), inplace=True) # Make all cols lowercase
        if 'mb2018_code' in df.columns:
            df['mb2018_code'] = pd.to_numeric(df['mb2018_code'], errors='coerce')
        return df
    except FileNotFoundError:
        print(f"Warning: {path} not found for Local Board mapping. LB summaries will be affected.")
        return pd.DataFrame()

# --- Functions replicating SAS Macros ---

def summarize_by_geo_predictor(df: pd.DataFrame, geo_col: str, predictor_col: str, incompleteness_vars: list) -> pd.DataFrame:
    """
    Replicates the core logic of SAS macros like %dhb (first version) or %taward (first version).
    Summarizes incompleteness by geography and a given predictor.
    """
    if df.empty or predictor_col not in df.columns or geo_col not in df.columns:
        return pd.DataFrame()

    # Ensure predictor_col is treated as categorical for grouping, handle NA by filling temporarily
    # Groupby in pandas by default excludes NA keys. SAS CLASS statement includes missing as a level.
    # To replicate SAS, we'd fillna for grouping, then potentially replace later if needed.
    # For this specific SAS macro, it seems it processes existing levels.

    # Ensure incompleteness_vars exist
    valid_incompleteness_vars = [v for v in incompleteness_vars if v in df.columns]
    if not valid_incompleteness_vars:
        print(f"Warning: None of {incompleteness_vars} found in DataFrame for predictor {predictor_col}.")
        return pd.DataFrame()

    agg_dict = {'total': ('snz_uid', 'count')} # Assuming snz_uid or any unique ID per child
    for var_name in valid_incompleteness_vars:
        agg_dict[var_name] = (var_name, 'sum')

    summary_df = df.groupby([geo_col, predictor_col], dropna=False).agg(**agg_dict).reset_index()
    summary_df.rename(columns={predictor_col: 'level'}, inplace=True)
    summary_df['var'] = predictor_col
    return summary_df

def summarize_completion_by_year(df: pd.DataFrame, geo_col: str = None) -> pd.DataFrame:
    """
    Replicates %NA(year) and %TA(year) macros for completion rates.
    If geo_col is None, it's a national summary by year.
    Otherwise, groups by year and geo_col.
    """
    if df.empty: return pd.DataFrame()

    completion_vars = ['vht_complete', 'nurse_complete', 'sdqt_complete']
    valid_completion_vars = [v for v in completion_vars if v in df.columns]
    if not valid_completion_vars:
        print(f"Warning: No completion vars {completion_vars} found in DataFrame.")
        return pd.DataFrame()

    agg_dict = {'total': ('snz_uid', 'count')}
    for var_name in valid_completion_vars:
        agg_dict[var_name] = (var_name, 'sum')

    group_by_cols = ['year']
    if geo_col:
        if geo_col not in df.columns:
            print(f"Warning: Geo column {geo_col} not found for yearly summary.")
            return pd.DataFrame()
        group_by_cols.append(geo_col)

    # Ensure year is suitable for grouping (e.g., not float with NaNs if it can be int)
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')

    summary_df = df.groupby(group_by_cols, dropna=False).agg(**agg_dict).reset_index()
    return summary_df


def summarize_national_by_predictor(df: pd.DataFrame, predictor_col: str, incompleteness_vars: list) -> pd.DataFrame:
    """
    Replicates the %nation(var) macro.
    Summarizes national incompleteness by a given predictor.
    """
    if df.empty or predictor_col not in df.columns:
        return pd.DataFrame()

    valid_incompleteness_vars = [v for v in incompleteness_vars if v in df.columns]
    if not valid_incompleteness_vars:
        print(f"Warning: None of {incompleteness_vars} found for national predictor {predictor_col}.")
        return pd.DataFrame()

    agg_dict = {'total': ('snz_uid', 'count')}
    for var_name in valid_incompleteness_vars:
        agg_dict[var_name] = (var_name, 'sum')

    summary_df = df.groupby([predictor_col], dropna=False).agg(**agg_dict).reset_index()
    summary_df.rename(columns={predictor_col: 'level'}, inplace=True)
    summary_df['var'] = predictor_col
    return summary_df

def get_missing_counts(df: pd.DataFrame, predictor_cols: list) -> pd.DataFrame:
    """
    Replicates the %MISSING(var) logic using PROC FREQ / MISSING OUT=.
    Calculates counts for each level including missing.
    """
    if df.empty: return pd.DataFrame()

    all_missing_counts = []
    for col in predictor_cols:
        if col not in df.columns:
            print(f"Warning: Column {col} not found for missing counts.")
            continue
        # value_counts(dropna=False) includes NaN as a level.
        # PROC FREQ / MISSING treats all missing values (numeric '.', .A, ._, char '') as one category.
        # For pandas, we fillna to a specific placeholder to group them.
        counts = df[col].fillna("MISSING_VAL_PLACEHOLDER").value_counts(dropna=False).reset_index()
        counts.columns = ['level', 'COUNT']
        counts['level'] = counts['level'].replace("MISSING_VAL_PLACEHOLDER", np.nan) # Show as NaN or specific string
        counts['var'] = col
        all_missing_counts.append(counts)

    if not all_missing_counts: return pd.DataFrame()
    return pd.concat(all_missing_counts, ignore_index=True)


def get_predictor_distribution_by_geo(df: pd.DataFrame, geo_col: str, predictor_col: str) -> pd.DataFrame:
    """
    Replicates %DHBpred(var) and %TApred(var) using PROC FREQ TABLE geo * predictor.
    """
    if df.empty or predictor_col not in df.columns or geo_col not in df.columns:
        return pd.DataFrame()

    # PROC FREQ table geo * predictor / NOPERCENT NOROW NOCOL MISSING OUT=
    # This creates counts for each combination of geo_col and predictor_col, including missing levels.
    # We can achieve this with groupby and size, then unstack, or using crosstab.
    # Using groupby().size() is often more straightforward for multi-level grouping.

    # Fill NA for grouping, as SAS PROC FREQ with /MISSING includes missing as a level
    df_filled = df[[geo_col, predictor_col]].copy()
    df_filled[geo_col] = df_filled[geo_col].fillna("MISSING_GEO")
    df_filled[predictor_col] = df_filled[predictor_col].fillna("MISSING_PRED")

    counts_df = df_filled.groupby([geo_col, predictor_col]).size().reset_index(name='COUNT')

    # Replace placeholders back to NaN or desired representation if needed
    counts_df.loc[counts_df[geo_col] == "MISSING_GEO", geo_col] = np.nan
    counts_df.loc[counts_df[predictor_col] == "MISSING_PRED", predictor_col] = np.nan

    counts_df.rename(columns={predictor_col: 'level'}, inplace=True)
    counts_df['var'] = predictor_col
    # SAS output from PROC FREQ OUT= has specific columns, here we mimic the essential ones.
    # The 'PERCENT' column was dropped in SAS, so we only need 'COUNT'.
    return counts_df


# --- Main Orchestration Function ---
def create_all_datalab_outputs(b4sc_allyr_df: pd.DataFrame, area_map_df: pd.DataFrame, output_dir: str = "."):
    if b4sc_allyr_df.empty:
        print("Main combined DataFrame is empty. Cannot create outputs.")
        return

    os.makedirs(output_dir, exist_ok=True)

    incompleteness_vars = ['vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']

    # Predictor list (from SAS macro calls) - ensure these columns exist in b4sc_allyr_df
    # Some predictors used in SAS might have slightly different names after Python conversion (e.g. hh_size_grp2 vs hh_size_grp)
    # For now, use names as they appear in the SAS macro calls.
    predictor_list_dhb_ta = [
        'n_mv_access', 'low_bw', 'sex', 'maori_eth', 'asian_eth', 'pacific_eth', 'euro_eth',
        'nzdep_quint', 'sibling_count', 'mother_highest_qual', 'hh_benefit_inc',
        'mother_age_grp', 'birth_father',
        # 'parent1_no_english', # This was dropped and recreated in combine_years.py
        'urban', 'hh_size_grp', # SAS used hh_size_grp2 for first dhb run, then hh_size_grp. Assuming hh_size_grp.
        'hh_rent', 'res_changes',
        # 'mother_smoke', # This variable might not have been created if parent1_smoke was not available
        'bw_grp',
        # 'gestation_grp', # This was dropped and recreated in combine_years.py
        # 'disability_flag', # This was dropped and recreated in combine_years.py
        'inpatient_visit_grp',
        # 'los_days_grp', # This was dropped in combine_years.py
        'ed_visit_grp', 'gp_visit_grp',
        # New predictors added in later SAS macro calls for dhb_full_data/taward_final
        'child_nz_born', 'mother_no_english', 'mother_nz_born', 'disability_flag', 'gestation_grp'
    ]
    # Filter for predictors actually present in the dataframe
    predictor_list_dhb_ta = [p for p in predictor_list_dhb_ta if p in b4sc_allyr_df.columns]


    # --- Output 1: dhb_full_data.csv (predictor summaries by DHB) ---
    print("Generating dhb_full_data...")
    all_dhb_summaries = []
    for pred_col in predictor_list_dhb_ta:
        summary = summarize_by_geo_predictor(b4sc_allyr_df, 'dhb2015_name', pred_col, incompleteness_vars)
        if not summary.empty:
            all_dhb_summaries.append(summary)
    if all_dhb_summaries:
        dhb_full_data_df = pd.concat(all_dhb_summaries, ignore_index=True)
        dhb_full_data_df.to_csv(os.path.join(output_dir, "dhb_full_data.csv"), index=False)
        print("dhb_full_data.csv generated.")
    else:
        print("No data for dhb_full_data.csv.")


    # --- Output 2: taward_final.csv (predictor summaries by TA/Ward, with all combinations) ---
    print("Generating taward_final...")
    all_taward_summaries = []
    # SAS uses 'grp_ta_ward_name' for the final version of this file
    for pred_col in predictor_list_dhb_ta: # SAS uses a slightly reduced list for TA later, but initial is full
        summary = summarize_by_geo_predictor(b4sc_allyr_df, 'grp_ta_ward_name', pred_col, incompleteness_vars)
        if not summary.empty:
             all_taward_summaries.append(summary)

    if all_taward_summaries:
        taward_full_data_intermediate_df = pd.concat(all_taward_summaries, ignore_index=True)

        # Create shell dataset with all combinations for taward_final
        # Get a complete list of all variables and levels from dhb_full_data (as per SAS logic)
        if not dhb_full_data_df.empty:
            varlevels_df = dhb_full_data_df[['var', 'level']].drop_duplicates().sort_values(by=['var', 'level'])

            # Complete list of ta_wards (using grp_ta_ward_name)
            # Ensure 'grp_ta_ward_name' exists
            if 'grp_ta_ward_name' in taward_full_data_intermediate_df.columns:
                tas_df = pd.DataFrame({'grp_ta_ward_name': taward_full_data_intermediate_df['grp_ta_ward_name'].unique()})
                tas_df.sort_values(by='grp_ta_ward_name', inplace=True)

                # Cartesian product
                ta_varlist_full_df = pd.merge(tas_df.assign(key=1), varlevels_df.assign(key=1), on='key').drop('key', axis=1)

                # SAS: Remove gestation, mother english and disability as we are not using them for the ta/ward analysis
                # This list might need adjustment based on exact R script needs later
                vars_to_remove_for_ta = ['disability_flag', 'parent1_no_english', 'gestation_grp',
                                         'father_highest_qual', 'los_days_grp'] # father_highest_qual not in list
                ta_varlist_df = ta_varlist_full_df[~ta_varlist_full_df['var'].isin(vars_to_remove_for_ta)]

                # Merge with original data files so that blanks are inserted for missing var levels
                taward_final_df = pd.merge(
                    ta_varlist_df,
                    taward_full_data_intermediate_df,
                    on=['grp_ta_ward_name', 'var', 'level'],
                    how='left'
                )
                taward_final_df.to_csv(os.path.join(output_dir, "taward_final.csv"), index=False)
                print("taward_final.csv generated.")
            else:
                print("Skipping taward_final.csv generation as 'grp_ta_ward_name' is missing from intermediate summary.")
        else:
            print("Skipping taward_final.csv as dhb_full_data_df was empty (needed for varlevels).")
    else:
        print("No data for taward_final.csv.")


    # --- Output 3: completion_all_year.csv (National completion by year) ---
    print("Generating completion_all_year...")
    completion_all_year_df = summarize_completion_by_year(b4sc_allyr_df)
    if not completion_all_year_df.empty:
        completion_all_year_df.to_csv(os.path.join(output_dir, "completion_all_year.csv"), index=False)
        print("completion_all_year.csv generated.")
    else:
        print("No data for completion_all_year.csv")

    # --- Output 4: completion_all_year_ta.csv (Completion by TA/Ward and year) ---
    print("Generating completion_all_year_ta...")
    completion_all_year_ta_df = summarize_completion_by_year(b4sc_allyr_df, geo_col='grp_ta_ward_name')
    if not completion_all_year_ta_df.empty:
        completion_all_year_ta_df.to_csv(os.path.join(output_dir, "completion_all_year_ta.csv"), index=False)
        print("completion_all_year_ta.csv generated.")
    else:
        print("No data for completion_all_year_ta.csv")

    # --- Output 5: national_incomplete.csv (National incompleteness by predictor) ---
    print("Generating national_incomplete...")
    all_national_predictor_summaries = []
    for pred_col in predictor_list_dhb_ta: # SAS uses a comprehensive list here
        summary = summarize_national_by_predictor(b4sc_allyr_df, pred_col, incompleteness_vars)
        if not summary.empty:
            all_national_predictor_summaries.append(summary)
    if all_national_predictor_summaries:
        national_incomplete_df = pd.concat(all_national_predictor_summaries, ignore_index=True)
        national_incomplete_df.to_csv(os.path.join(output_dir, "national_incomplete.csv"), index=False)
        print("national_incomplete.csv generated.")
    else:
        print("No data for national_incomplete.csv")


    # --- Output 6: missing_count.csv (Missing counts for each predictor) ---
    print("Generating missing_count...")
    # Predictor list for missing counts is slightly different in SAS, includes most from predictor_list_dhb_ta
    missing_count_df = get_missing_counts(b4sc_allyr_df, predictor_list_dhb_ta)
    if not missing_count_df.empty:
        missing_count_df.to_csv(os.path.join(output_dir, "missing_count.csv"), index=False)
        print("missing_count.csv generated.")
    else:
        print("No data for missing_count.csv")

    # --- Output 7: pred_dist_DHB.csv (Predictor distribution by DHB) ---
    print("Generating pred_dist_DHB...")
    all_pred_dist_dhb = []
    for pred_col in predictor_list_dhb_ta:
        dist_df = get_predictor_distribution_by_geo(b4sc_allyr_df, 'dhb2015_name', pred_col)
        if not dist_df.empty:
            all_pred_dist_dhb.append(dist_df)
    if all_pred_dist_dhb:
        pred_dist_dhb_df = pd.concat(all_pred_dist_dhb, ignore_index=True)
        pred_dist_dhb_df.to_csv(os.path.join(output_dir, "pred_dist_DHB.csv"), index=False)
        print("pred_dist_DHB.csv generated.")
    else:
        print("No data for pred_dist_DHB.csv")

    # --- Output 8: pred_dist_TA.csv (Predictor distribution by TA/Ward) ---
    print("Generating pred_dist_TA...")
    all_pred_dist_ta = []
    for pred_col in predictor_list_dhb_ta:
        dist_df = get_predictor_distribution_by_geo(b4sc_allyr_df, 'grp_ta_ward_name', pred_col)
        if not dist_df.empty:
            all_pred_dist_ta.append(dist_df)
    if all_pred_dist_ta:
        pred_dist_ta_df = pd.concat(all_pred_dist_ta, ignore_index=True)
        pred_dist_ta_df.to_csv(os.path.join(output_dir, "pred_dist_TA.csv"), index=False)
        print("pred_dist_TA.csv generated.")
    else:
        print("No data for pred_dist_TA.csv")

    # --- Local Board Summaries ---
    print("Generating Local Board summaries...")
    if area_map_df.empty or 'mb18_num' not in b4sc_allyr_df.columns:
        print("Skipping Local Board summaries as area map or mb18_num is missing.")
    else:
        # Merge b4sc_allyr_df with area_map_df to get Local Board (CB2018_name)
        # Ensure consistent column names for merging (e.g. 'mb18_num' and 'mb2018_code')
        b4sc_allyr_df['mb18_num'] = pd.to_numeric(b4sc_allyr_df['mb18_num'], errors='coerce')

        dataset_for_lb = pd.merge(
            b4sc_allyr_df,
            area_map_df[['mb2018_code', 'ta2018_name', 'cb2018_name']], # Use lowercase from helper
            left_on='mb18_num',
            right_on='mb2018_code',
            how='left'
        )

        # Filter for Auckland DHBs
        auckland_dhbs = ["Auckland", "Counties Manukau", "Waitemata"]
        # dhb2015_name might have had quotes removed in combine_years.py
        dataset2_lb = dataset_for_lb[dataset_for_lb['dhb2015_name'].isin(auckland_dhbs)].copy()

        if not dataset2_lb.empty:
            # Combine specific Local Boards: "Great Barrier and Waiheke" and "Waitemata"
            # This logic is complex in SAS with intermediate data steps.
            # Python equivalent: identify rows, sum their values, create new rows, append, then filter out old ones.
            lb_to_combine1 = "Great Barrier and Waiheke"
            lb_to_combine2 = "Waitemata"
            combined_lb_name = "Great Barrier, Waiheke and Waitemata"

            # Logic for completion_all_year_LB.csv
            completion_lb_data = dataset2_lb.copy()
            # Group by year and cb2018_name first for original LBs
            lb_completion_orig = summarize_completion_by_year(completion_lb_data, geo_col='cb2018_name')

            rows_to_combine_lb = lb_completion_orig[lb_completion_orig['cb2018_name'].isin([lb_to_combine1, lb_to_combine2])]
            if not rows_to_combine_lb.empty:
                combined_sum_lb = rows_to_combine_lb.groupby('year').agg(
                    total=('total', 'sum'),
                    vht_complete=('vht_complete', 'sum'),
                    nurse_complete=('nurse_complete', 'sum'),
                    sdqt_complete=('sdqt_complete', 'sum')
                ).reset_index()
                combined_sum_lb['cb2018_name'] = combined_lb_name
                # Need to determine DHB for this combined group if it's used further (SAS takes from first row)
                # For now, just the combined data as per sum.

                completion_all_year_lb_df = pd.concat([
                    lb_completion_orig[~lb_completion_orig['cb2018_name'].isin([lb_to_combine1, lb_to_combine2])],
                    combined_sum_lb
                ], ignore_index=True)
                # SAS also filters out Onewhero-Tuakau, and empty DHB names
                completion_all_year_lb_df = completion_all_year_lb_df[
                    (completion_all_year_lb_df['cb2018_name'] != "Onewhero-Tuakau") &
                    (completion_all_year_lb_df['cb2018_name'].notna()) # Assuming empty DHB name means cb name is also na
                ]
                completion_all_year_lb_df.to_csv(os.path.join(output_dir, "completion_all_year_LB.csv"), index=False)
                print("completion_all_year_LB.csv generated.")

            # Logic for lb_full_data.csv (predictor summaries by LB)
            all_lb_predictor_summaries = []
            for pred_col in predictor_list_dhb_ta: # SAS uses same predictor list as dhb/ta
                 summary = summarize_by_geo_predictor(dataset2_lb, 'cb2018_name', pred_col, incompleteness_vars)
                 if not summary.empty:
                    all_lb_predictor_summaries.append(summary)

            if all_lb_predictor_summaries:
                lb_full_data0_df = pd.concat(all_lb_predictor_summaries, ignore_index=True)

                # Combine specific LBs in this summary table too
                rows_to_combine_pred_lb = lb_full_data0_df[lb_full_data0_df['cb2018_name'].isin([lb_to_combine1, lb_to_combine2])]
                if not rows_to_combine_pred_lb.empty:
                    combined_sum_pred_lb = rows_to_combine_pred_lb.groupby(['var', 'level']).agg(
                        total=('total', 'sum'),
                        vht_incomplete=('vht_incomplete', 'sum'),
                        nurse_incomplete=('nurse_incomplete', 'sum'),
                        sdqt_incomplete=('sdqt_incomplete', 'sum')
                    ).reset_index()
                    combined_sum_pred_lb['cb2018_name'] = combined_lb_name

                    lb_full_data_df = pd.concat([
                        lb_full_data0_df[~lb_full_data0_df['cb2018_name'].isin([lb_to_combine1, lb_to_combine2])],
                        combined_sum_pred_lb
                    ], ignore_index=True)
                    # Filter out Onewhero-Tuakau and original components of combined LBs
                    lb_full_data_df = lb_full_data_df[
                        ~lb_full_data_df['cb2018_name'].isin([lb_to_combine1, lb_to_combine2, "Onewhero-Tuakau"])
                    ]
                else:
                    lb_full_data_df = lb_full_data0_df[~lb_full_data0_df['cb2018_name'].isin(["Onewhero-Tuakau"])]


                # Small number suppression (values < 6 set to missing/NaN)
                cols_to_suppress = ['total', 'vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']
                for col in cols_to_suppress:
                    if col in lb_full_data_df.columns:
                        lb_full_data_df.loc[lb_full_data_df[col] < 6, col] = np.nan

                lb_full_data_df.to_csv(os.path.join(output_dir, "lb_full_data.csv"), index=False)
                print("lb_full_data.csv generated.")
            else:
                print("No data for lb_full_data.csv intermediate summaries.")
        else:
            print("No data for Auckland DHBs after filtering for Local Board summaries.")


# --- Script Execution ---
if __name__ == "__main__":
    print("--- Main execution for creating Datalab output files started ---")

    main_df = load_combined_b4sc_data()
    areas_df = load_annual_areas_2018() # Used for Local Board mapping

    if not main_df.empty:
        create_all_datalab_outputs(main_df, areas_df, output_dir="datalab_outputs_python")
        print("\nAll Datalab output files processing attempted.")
        print(f"Please check the '{os.path.abspath('datalab_outputs_python')}' directory.")
    else:
        print("Could not load main input data. Exiting.")

    print("--- Main execution finished ---")
```
