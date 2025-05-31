import pandas as pd
import numpy as np
# For potential statistical calculations, though not explicitly used for RR CI formula in R script
# from scipy import stats

# Matplotlib/Seaborn would be imported here in a full plotting script
# import matplotlib.pyplot as plt
# import seaborn as sns

# --- Global Variables & Settings ---
# Color palette from R script
SWA_COLOR_PALETTE = [
    "#ff0000", "#6b9b5f", "#2a2a3e", "#2c86b4", "#E8731B", "#007e87",
    "#3a9cea", "#db9824", "#366a59", "#26567f"
]

# --- Data Loading Functions ---
def load_csv_data(filename: str, **kwargs) -> pd.DataFrame:
    """Helper function to load CSV data with error handling."""
    print(f"Loading {filename}...")
    try:
        return pd.read_csv(filename, **kwargs)
    except FileNotFoundError:
        print(f"Warning: File {filename} not found. Returning empty DataFrame.")
        return pd.DataFrame()

# --- Initial Data Processing ---
# Load main datasets (paths might need adjustment based on actual file locations)
dhb_map_df = load_csv_data("dhb_map.csv")
var_labs_df = load_csv_data("list of var levels.csv", header=None, names=['V1', 'V2', 'V3', 'V4', 'V5'])

com_all_year_df = load_csv_data("completion_all_year.csv")
com_all_year_ta_df = load_csv_data("completion_all_year_ta.csv")

# Calculate national level completion rate
if not com_all_year_df.empty:
    com_all_year_df['vht_rate'] = pd.to_numeric(com_all_year_df['vht_complete'], errors='coerce') / pd.to_numeric(com_all_year_df['total'], errors='coerce')
    com_all_year_df['nurse_rate'] = pd.to_numeric(com_all_year_df['nurse_complete'], errors='coerce') / pd.to_numeric(com_all_year_df['total'], errors='coerce')
    com_all_year_df['sdqt_rate'] = pd.to_numeric(com_all_year_df['sdqt_complete'], errors='coerce') / pd.to_numeric(com_all_year_df['total'], errors='coerce')

# Map TA to DHB for TA-level completion data
if not com_all_year_ta_df.empty and not dhb_map_df.empty:
    com_all_year_ta_df = pd.merge(com_all_year_ta_df, dhb_map_df, left_on="grp_ta_ward_name", right_on="WARD2013_name", how="left")
    # Check for NAs after merge, similar to table(com_all_year_ta$grp_ta_ward_name[is.na(com_all_year_ta$DHB_name)])
    # print("TAs with no DHB match:", com_all_year_ta_df[com_all_year_ta_df['DHB_name'].isna()]['grp_ta_ward_name'].unique())

    com_all_year_ta_df['vht_rate'] = pd.to_numeric(com_all_year_ta_df['vht_complete'], errors='coerce') / pd.to_numeric(com_all_year_ta_df['total'], errors='coerce')
    com_all_year_ta_df['nurse_rate'] = pd.to_numeric(com_all_year_ta_df['nurse_complete'], errors='coerce') / pd.to_numeric(com_all_year_ta_df['total'], errors='coerce')
    com_all_year_ta_df['sdqt_rate'] = pd.to_numeric(com_all_year_ta_df['sdqt_complete'], errors='coerce') / pd.to_numeric(com_all_year_ta_df['total'], errors='coerce')

# For each DHB, attach one row for national average to TA data
com_all_year_final_df = pd.DataFrame() # Initialize
if not com_all_year_df.empty and not dhb_map_df.empty and not com_all_year_ta_df.empty:
    data1 = com_all_year_df[['YEAR', 'vht_rate', 'nurse_rate', 'sdqt_rate']]
    # Create a DataFrame with unique DHB names to merge with national data
    unique_dhbs = pd.DataFrame({'DHB_name': dhb_map_df['DHB_name'].unique()})
    # Cross join national averages with unique DHB names
    data3 = pd.merge(data1.assign(key=1), unique_dhbs.assign(key=1), on='key').drop('key', axis=1)
    data3['grp_ta_ward_name'] = "National average"

    com_all_year_final_df = pd.concat([com_all_year_ta_df, data3], ignore_index=True)
    com_all_year_final_df['vht_rate_perc'] = round(com_all_year_final_df['vht_rate'] * 100, 2)
    com_all_year_final_df['nurse_rate_perc'] = round(com_all_year_final_df['nurse_rate'] * 100, 2)
    com_all_year_final_df['sdqt_rate_perc'] = round(com_all_year_final_df['sdqt_rate'] * 100, 2)
else:
    print("Warning: Could not create 'com_all_year_final_df' due to missing initial data.")


# --- Plotting Functions for Attendance by Module and Year (TA/Ward level) ---
def prepare_attendance_plot_data(dhb_name: str, source_df: pd.DataFrame, geo_col_name: str) -> pd.DataFrame:
    """ Helper to prepare data for myplot_* functions """
    if source_df.empty or dhb_name not in source_df['DHB_name'].unique():
        print(f"Warning: DHB {dhb_name} not found or source_df is empty.")
        return pd.DataFrame()

    to_plot_df = source_df[source_df['DHB_name'] == dhb_name].copy()

    # Order factor levels for geo_col_name (e.g., grp_ta_ward_name or CB2018_name)
    # to make "National average" appear first in legend/plot
    if geo_col_name in to_plot_df.columns:
        geo_levels = to_plot_df[geo_col_name].astype('category').cat.categories.tolist()
        if "National average" in geo_levels:
            idx_na = geo_levels.index("National average")
            ordered_levels = [geo_levels[idx_na]] + [lvl for i, lvl in enumerate(geo_levels) if i != idx_na]
            to_plot_df[geo_col_name] = pd.Categorical(to_plot_df[geo_col_name], categories=ordered_levels, ordered=True)
    return to_plot_df

def plot_attendance_rate(df: pd.DataFrame, rate_col_name: str, title: str, y_axis_label: str = "", x_axis_label: str = "", geo_col_name: str = 'grp_ta_ward_name', y_limits=(50,100)):
    """
    Generic plotting function structure for attendance rates.
    Actual plotting with matplotlib/seaborn would go here.
    """
    if df.empty:
        print(f"No data provided for plotting: {title}")
        return

    print(f"\n--- Data for: {title} ({df[geo_col_name].nunique()} groups) ---")
    # print(df[['YEAR', rate_col_name, geo_col_name]].head())
    print(f"Plotting: {title} for {df['DHB_name'].iloc[0] if 'DHB_name' in df.columns else 'Unknown DHB'}")
    print(f"Rate column: {rate_col_name}, Y-limits: {y_limits}")

    # --- Matplotlib/Seaborn plotting would start here ---
    # Example (very basic, R version is more complex with manual scales):
    # plt.figure(figsize=(10, 6))
    # for i, group in enumerate(df[geo_col_name].unique()):
    #     group_df = df[df[geo_col_name] == group]
    #     plt.plot(group_df['YEAR'], group_df[rate_col_name], marker='o',
    #              label=group, color=SWA_COLOR_PALETTE[i % len(SWA_COLOR_PALETTE)],
    #              linestyle='--' if group == "National average" else '-')
    # plt.title(title)
    # plt.xlabel(x_axis_label if x_axis_label else "Year (e.g., 11/12 for 2011)")
    # plt.ylabel(y_axis_label if y_axis_label else "Attendance Rate (%)")
    # plt.ylim(y_limits)
    # year_breaks = sorted(df['YEAR'].unique())
    # year_labels = [f"{str(y)[-2:]}/{str(y+1)[-2:]}" for y in year_breaks]
    # plt.xticks(ticks=year_breaks, labels=year_labels)
    # plt.legend(title=geo_col_name, bbox_to_anchor=(1.05, 1), loc='upper left')
    # plt.grid(True, axis='y', linestyle=':')
    # plt.tight_layout()
    # plt.show() # or save to file
    # --- End of Matplotlib/Seaborn plotting ---
    pass


def myplot_vht(dhb_name: str, source_df=com_all_year_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'grp_ta_ward_name')
    plot_attendance_rate(plot_data, 'vht_rate_perc', "VHT Attendance Rates (%)", y_limits=(50,100))

def myplot_nurse(dhb_name: str, source_df=com_all_year_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'grp_ta_ward_name')
    plot_attendance_rate(plot_data, 'nurse_rate_perc', "Nurse Attendance Rates (%)", y_limits=(50,100))

def myplot_sdqt(dhb_name: str, source_df=com_all_year_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'grp_ta_ward_name')
    plot_attendance_rate(plot_data, 'sdqt_rate_perc', "SDQ-Teacher Attendance Rates (%)", y_limits=(0,100))


# --- Local Board Data Processing and Plotting Functions ---
com_all_year_lb_df = load_csv_data("completion_all_year_LB.csv")
com_all_year_lb_final_df = pd.DataFrame() # Initialize

if not com_all_year_lb_df.empty:
    # Combine "Great Barrier and Waiheke" and "Waitemata" LBs
    rows_to_combine_c = []
    for year_val in com_all_year_lb_df['YEAR'].unique():
        a = com_all_year_lb_df[
            (com_all_year_lb_df['CB2018_name'].isin(["Great Barrier and Waiheke", "Waitemata"])) &
            (com_all_year_lb_df['YEAR'] == year_val)
        ]
        if not a.empty:
            b = pd.DataFrame({
                'CB2018_name': ["Great Barrier, Waiheke and Waitemata"],
                'total': [a['total'].sum()],
                'vht_complete': [a['vht_complete'].sum()],
                'nurse_complete': [a['nurse_complete'].sum()],
                'sdqt_complete': [a['sdqt_complete'].sum()],
                'YEAR': [year_val],
                'DHB_name': [a['DHB_name'].iloc[0] if not a.empty else None] # Assuming DHB is same for these LBs in a year
            })
            rows_to_combine_c.append(b)

    if rows_to_combine_c:
        combined_lbs_df = pd.concat(rows_to_combine_c, ignore_index=True)
        com_all_year_lb_df = pd.concat([com_all_year_lb_df, combined_lbs_df], ignore_index=True)

    com_all_year_lb_df = com_all_year_lb_df[
        com_all_year_lb_df['DHB_name'].notna() & (com_all_year_lb_df['DHB_name'] != "") &
        ~com_all_year_lb_df['CB2018_name'].isin(["Great Barrier and Waiheke", "Waitemata", "Onewhero-Tuakau"])
    ].copy()

    com_all_year_lb_df['vht_rate'] = pd.to_numeric(com_all_year_lb_df['vht_complete'], errors='coerce') / pd.to_numeric(com_all_year_lb_df['total'], errors='coerce')
    com_all_year_lb_df['nurse_rate'] = pd.to_numeric(com_all_year_lb_df['nurse_complete'], errors='coerce') / pd.to_numeric(com_all_year_lb_df['total'], errors='coerce')
    com_all_year_lb_df['sdqt_rate'] = pd.to_numeric(com_all_year_lb_df['sdqt_complete'], errors='coerce') / pd.to_numeric(com_all_year_lb_df['total'], errors='coerce')

    # Add national average to LB data
    if not com_all_year_df.empty and not dhb_map_df.empty: # Ensure base data is available
        data1_lb = com_all_year_df[['YEAR', 'vht_rate', 'nurse_rate', 'sdqt_rate']]
        # Use unique DHBs from Auckland area for LB plots context if desired, or all DHBs
        # R script uses unique(dhb_map$DHB_name) implies all DHBs get this national line
        unique_dhbs_lb = pd.DataFrame({'DHB_name': dhb_map_df['DHB_name'].unique()})
        data3_lb = pd.merge(data1_lb.assign(key=1), unique_dhbs_lb.assign(key=1), on='key').drop('key', axis=1)
        data3_lb['CB2018_name'] = "National average"

        com_all_year_lb_final_df = pd.concat([com_all_year_lb_df, data3_lb], ignore_index=True)
        com_all_year_lb_final_df['vht_rate_perc'] = round(com_all_year_lb_final_df['vht_rate'] * 100, 2)
        com_all_year_lb_final_df['nurse_rate_perc'] = round(com_all_year_lb_final_df['nurse_rate'] * 100, 2)
        com_all_year_lb_final_df['sdqt_rate_perc'] = round(com_all_year_lb_final_df['sdqt_rate'] * 100, 2)
    else:
        print("Warning: Could not create 'com_all_year_lb_final_df' due to missing initial data.")
else:
    print("Warning: 'com_all_year_lb.csv' not loaded or empty. LB plots will not be generated correctly.")


def myplot_vht_lb(dhb_name: str, source_df=com_all_year_lb_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'CB2018_name')
    lower_limit = 40 if dhb_name == "Waitemata" else 50
    plot_attendance_rate(plot_data, 'vht_rate_perc', f"VHT Attendance Rates (%) by Local Board - {dhb_name}", geo_col_name='CB2018_name', y_limits=(lower_limit,100))

def myplot_nurse_lb(dhb_name: str, source_df=com_all_year_lb_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'CB2018_name')
    lower_limit = 40 if dhb_name == "Waitemata" else 50
    plot_attendance_rate(plot_data, 'nurse_rate_perc', f"Nurse Attendance Rates (%) by Local Board - {dhb_name}", geo_col_name='CB2018_name', y_limits=(lower_limit,100))

def myplot_sdqt_lb(dhb_name: str, source_df=com_all_year_lb_final_df):
    plot_data = prepare_attendance_plot_data(dhb_name, source_df, 'CB2018_name')
    plot_attendance_rate(plot_data, 'sdqt_rate_perc', f"SDQ-Teacher Attendance Rates (%) by Local Board - {dhb_name}", geo_col_name='CB2018_name', y_limits=(0,100))


# --- Forest Plot Data Preparation and Functions ---
dhb_incomplete_df = load_csv_data("dhb_fulldata.csv") # R script calls it dhb_fulldata.csv, SAS was dhb_full_data
all_plot_data_df = pd.DataFrame() # Initialize

if not dhb_incomplete_df.empty and not var_labs_df.empty:
    dhb_incomplete_df = pd.merge(dhb_incomplete_df, var_labs_df, left_on=["var", "level"], right_on=["V1", "V2"], how="left")
    dhb_incomplete_df.rename(columns={"V4": "var_label", "V5": "level_label", "V3": "ref_level_indicator"}, inplace=True)

    # Clean labels
    dhb_incomplete_df['var_label'] = dhb_incomplete_df['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False)
    dhb_incomplete_df['level_label'] = dhb_incomplete_df['level_label'].str.replace("Tertiary below Bachelor", "Tertiary", regex=False)
    dhb_incomplete_df['level_label'] = dhb_incomplete_df['level_label'].str.replace("No qualifications", "No quals", regex=False)

    # Attach ref values
    ref_values_df = dhb_incomplete_df[dhb_incomplete_df['ref_level_indicator'] == "ref"].copy()
    ref_values_df = ref_values_df[['var', 'DHB2015_name', 'total', 'vht_incomplete', 'nurse_incomplete', 'sdqt_incomplete']]
    ref_values_df.rename(columns={
        'total': 'ref_total', 'vht_incomplete': 'ref_vht',
        'nurse_incomplete': 'ref_nurse', 'sdqt_incomplete': 'ref_sdqt'
    }, inplace=True)

    dhb_incomplete_ref_df = pd.merge(dhb_incomplete_df, ref_values_df, on=["var", "DHB2015_name"], how="left")

    # Calculate RR
    for col_type in ['vht', 'nurse', 'sdqt']:
        incomplete_col = f'{col_type}_incomplete'
        ref_incomplete_col = f'ref_{col_type}'
        rr_col = f'rr_{col_type}'

        # Ensure columns are numeric and exist
        for c in [incomplete_col, 'total', ref_incomplete_col, 'ref_total']:
            if c in dhb_incomplete_ref_df.columns:
                dhb_incomplete_ref_df[c] = pd.to_numeric(dhb_incomplete_ref_df[c], errors='coerce')
            else: # Add missing column if not present (e.g. from empty placeholder load)
                dhb_incomplete_ref_df[c] = np.nan


        rate_group = dhb_incomplete_ref_df[incomplete_col] / dhb_incomplete_ref_df['total']
        rate_ref_group = dhb_incomplete_ref_df[ref_incomplete_col] / dhb_incomplete_ref_df['ref_total']

        # Avoid division by zero if ref rate is 0
        dhb_incomplete_ref_df[rr_col] = np.where(
            (dhb_incomplete_ref_df['ref_level_indicator'] == "") & (rate_ref_group > 0),
            rate_group / rate_ref_group,
            np.nan
        )

    # Calculate CIs
    for col_type in ['vht', 'nurse', 'sdqt']:
        incomplete_col = f'{col_type}_incomplete'
        ref_incomplete_col = f'ref_{col_type}'
        rr_col = f'rr_{col_type}'
        ci_col = f'ci_{col_type}'
        ci_ll_col = f'{col_type}_ci_ll'
        ci_ul_col = f'{col_type}_ci_ul'

        # Numerator for SE formula: ( (total - incomplete) / incomplete ) / total
        # Ensure no division by zero for 'incomplete' or 'total'
        term1_val_x1 = dhb_incomplete_ref_df[incomplete_col]
        term1_val_n1 = dhb_incomplete_ref_df['total']
        term1 = np.where((term1_val_x1 > 0) & (term1_val_n1 > 0), (((term1_val_n1 - term1_val_x1) / term1_val_x1) / term1_val_n1), np.nan)

        term2_val_x2 = dhb_incomplete_ref_df[ref_incomplete_col]
        term2_val_n2 = dhb_incomplete_ref_df['ref_total']
        term2 = np.where((term2_val_x2 > 0) & (term2_val_n2 > 0), (((term2_val_n2 - term2_val_x2) / term2_val_x2) / term2_val_n2), np.nan)

        # Avoid sqrt of negative or NaN
        se_val_squared = term1 + term2
        dhb_incomplete_ref_df[ci_col] = np.where(se_val_squared > 0, 1.96 * np.sqrt(se_val_squared), np.nan)

        # Avoid log(0) or log(NaN) for rr_col
        log_rr = np.where(dhb_incomplete_ref_df[rr_col] > 0, np.log(dhb_incomplete_ref_df[rr_col]), np.nan)

        dhb_incomplete_ref_df[ci_ll_col] = np.exp(log_rr - dhb_incomplete_ref_df[ci_col])
        dhb_incomplete_ref_df[ci_ul_col] = np.exp(log_rr + dhb_incomplete_ref_df[ci_col])

    # Prepare data for plotting (allplotdata in R)
    all_plot_data_df = dhb_incomplete_ref_df.copy()
    all_plot_data_df['varlevel'] = all_plot_data_df['var_label'].fillna('') + ": " + all_plot_data_df['level_label'].fillna('')

    # Apply string replacements for varlevel
    replacements = {
        "N changes of residence to age 4": "Address changes",
        "Received disability support: Yes": "Disability support",
        "N inpatient hospital visits": "N inpatient visits",
        "N quarters enrolled GP": "N qtrs enrolled GP",
        "Rented home: Yes": "Rented home",
        "Pacific ethnicity: Yes": "Pacific ethnicity",
        "Mother speaks English: Yes [(]vs No[)]": "Mother speaks English", # Literal brackets need escaping if regex=True
        "Mother was born in NZ: Yes [(]vs No[)]": "Mother born in NZ",
        "Maori ethnicity: Yes": "Maori ethnicity",
        "European ethnicity: Yes": "European ethnicity",
        "ED visit ever: Yes": "ED visit ever",
        "Birthweight <2500g: Yes": "Birthweight <2500g",
        "Child was born in NZ: Yes [(]vs No[)]": "Child born in NZ",
        "Benefit income: Yes": "Benefit income",
        "Asian ethnicity: Yes": "Asian ethnicity",
        "Mother high qual: Tertiary": "Mother tertiary qual",
        "Mother high qual: No quals": "Mother no quals",
        "Mother high qual: High school": "Mother high school qual",
        "N motor vehicles available": "N motor vehicles",
        "Sex: Male [(]vs Female[)]": "Male",
        "Maori ethnicity": "M\u0101ori ethnicity" # Unicode for macron a
    }
    for old, new in replacements.items():
        all_plot_data_df['varlevel'] = all_plot_data_df['varlevel'].str.replace(old, new, regex=False) # Use regex=False for literal replace

    all_plot_data_df = all_plot_data_df[all_plot_data_df['ref_level_indicator'] == ""].copy()
    all_plot_data_df = all_plot_data_df[~all_plot_data_df['var'].isin(["los_days_grp", "bw_grp"])].copy()

    # Factor ordering for varlevelnew and batch (complex in R, simplified here)
    # This ordering is crucial for the plot's appearance.
    # For Python, this would typically be done by creating a CategoricalDtype.
    # The R script uses specific indices which is hard to maintain.
    # A more robust way would be to define the order explicitly or based on another column.
    # For now, we'll skip the exact reordering of varlevelnew and batch, as it's display logic.
    # It's important for the plot, but the data is prepared up to this point.
    # Add placeholder for batch column
    # Define batch categories based on var_label (simplified from R's factor level manipulation)
    def assign_batch(var_label):
        if var_label in ["N motor vehicles", "Mother high qual", "NZDep", "Rented home", "Benefit income"]:
            return "Family Socioeconomic Position"
        elif var_label in ["N qtrs enrolled GP", "Disability support", "Birthweight <2500g", "Gestation", "ED visit ever", "N inpatient visits"]:
            return "Health & Health System"
        else: # Default for others like ethnicity, mother age, etc.
            return "Family & Child Characteristics"

    if 'var_label' in all_plot_data_df.columns:
        all_plot_data_df['batch'] = all_plot_data_df['var_label'].apply(assign_batch)
        # Order batch for faceting (optional, but good for consistency)
        batch_order = ["Family Socioeconomic Position", "Family & Child Characteristics", "Health & Health System"]
        all_plot_data_df['batch'] = pd.Categorical(all_plot_data_df['batch'], categories=batch_order, ordered=True)
    else:
        all_plot_data_df['batch'] = "Unknown"

else:
    print("Warning: 'dhb_fulldata.csv' or 'list of var levels.csv' not loaded. Forest plot data not prepared.")


def pred_forest_plot(dhb_name: str, module_type: str, source_df=all_plot_data_df):
    """
    Prepares data and defines structure for forest plots.
    `module_type` should be 'vht', 'nurse', or 'sdqt'.
    """
    if source_df.empty:
        print(f"No data for forest plot for DHB: {dhb_name}, Module: {module_type}")
        return

    plot_data = source_df[source_df['DHB2015_name'] == dhb_name].copy()
    rr_col = f'rr_{module_type}'
    ci_ll_col = f'{module_type}_ci_ll'
    ci_ul_col = f'{module_type}_ci_ul'

    plot_data = plot_data[plot_data[rr_col].notna() & (plot_data[rr_col] != "")]

    if plot_data.empty:
        print(f"No valid RR data for forest plot for DHB: {dhb_name}, Module: {module_type}")
        return

    # Determine upper limit for plot (dynamic as in R)
    # This logic is simplified; R script has specific values per DHB.
    # A more robust approach would be to calculate max from ci_ul_col for the specific dhb.
    upper_limit = plot_data[ci_ul_col].max() if not plot_data.empty else 10
    upper_limit = max(upper_limit, 3.5) # ensure a minimum range
    upper_limit = min(upper_limit, 20)  # cap at a reasonable max if some CIs are huge
    if pd.isna(upper_limit): upper_limit = 10


    print(f"\n--- Data for Forest Plot: {dhb_name} DHB - Module: {module_type.upper()} ---")
    # print(plot_data[['varlevel', rr_col, ci_ll_col, ci_ul_col, 'batch']].head())
    print(f"Plotting Forest Plot for {dhb_name}, {module_type.upper()}. X-axis limit approx: {upper_limit:.1f}")

    # --- Matplotlib/Seaborn plotting would go here ---
    # This would involve creating a faceted plot by 'batch', with point ranges for RR and CIs.
    # Example for one point range:
    # plt.errorbar(x=plot_data[rr_col], y=plot_data['varlevelnew'], xerr=(plot_data[rr_col] - plot_data[ci_ll_col], plot_data[ci_ul_col] - plot_data[rr_col]), fmt='o')
    # plt.axvline(x=1, linestyle='--')
    # plt.xscale('log')
    # ... and much more for facets, colors, labels, themes.
    pass

def pred_forest_vht(dhb_name: str): pred_forest_plot(dhb_name, 'vht')
def pred_forest_nurse(dhb_name: str): pred_forest_plot(dhb_name, 'nurse')
def pred_forest_sdqt(dhb_name: str): pred_forest_plot(dhb_name, 'sdqt')

# R script has pred_forest_vht_1, _2 etc. These seem to be identical to the main ones
# but perhaps were intended for different DHB groups or plot variations.
# For Python, we'll assume the main functions are called with different DHB names.


# --- Predictor Composition Plot Data Preparation ---
pred_missing_count_df = load_csv_data("missing_count.csv") # National distribution
pred_dist_dhb_df = load_csv_data("pred_dist_dhb.csv") # DHB level distribution
pred_dhb_perc_full_df = pd.DataFrame() # Initialize

if not pred_missing_count_df.empty and not pred_dist_dhb_df.empty and not var_labs_df.empty:
    # National percentages
    pred_total_nat = pred_missing_count_df[pred_missing_count_df['level'] != "Missing"].copy()
    pred_total_nat['COUNT'] = pd.to_numeric(pred_total_nat['COUNT'], errors='coerce')
    pred_total_nat = pred_total_nat.groupby('var')['COUNT'].sum().reset_index().rename(columns={'COUNT': 'var_total'})

    pred_perc_nat = pd.merge(pred_missing_count_df, pred_total_nat, on='var', how='left')
    pred_perc_nat = pred_perc_nat[pred_perc_nat['level'] != "Missing"].copy()
    pred_perc_nat['COUNT'] = pd.to_numeric(pred_perc_nat['COUNT'], errors='coerce')
    pred_perc_nat['level'] = pred_perc_nat['level'].astype(str) # Ensure level is str for merge
    pred_perc_nat['perc_national'] = pred_perc_nat['COUNT'] / pred_perc_nat['var_total']

    # DHB percentages
    pred_dist_dhb_df_valid = pred_dist_dhb_df[
        (pred_dist_dhb_df['level'] != "MISSING") & (pred_dist_dhb_df['DHB2015_name'] != "") & pd.notna(pred_dist_dhb_df['level'])
    ].copy()
    pred_dist_dhb_df_valid['COUNT'] = pd.to_numeric(pred_dist_dhb_df_valid['COUNT'], errors='coerce')
    pred_dist_dhb_total = pred_dist_dhb_df_valid.groupby(['DHB2015_name', 'var'])['COUNT'].sum().reset_index().rename(columns={'COUNT': 'var_total_dhb'})

    pred_dhb_perc = pd.merge(pred_dist_dhb_df_valid, pred_dist_dhb_total, on=['DHB2015_name', 'var'], how='left')
    pred_dhb_perc['perc_dhb'] = pred_dhb_perc['COUNT'] / pred_dhb_perc['var_total_dhb']
    pred_dhb_perc['level'] = pred_dhb_perc['level'].astype(str) # Ensure level is str for merge

    # Merge DHB with national
    pred_dhb_perc_merged = pd.merge(pred_dhb_perc, pred_perc_nat[['var', 'level', 'perc_national']], on=['var', 'level'], how='left')
    pred_dhb_perc_merged['perc_diff'] = round((pred_dhb_perc_merged['perc_dhb'] - pred_dhb_perc_merged['perc_national']) * 100, 2)

    # Merge with var_labs
    var_labs_df_str_levels = var_labs_df.copy()
    var_labs_df_str_levels['V2'] = var_labs_df_str_levels['V2'].astype(str) # Ensure level is str for merge
    pred_dhb_perc_full_df = pd.merge(var_labs_df_str_levels, pred_dhb_perc_merged, left_on=['V1', 'V2'], right_on=['var', 'level'], how='right')
    pred_dhb_perc_full_df.rename(columns={'V4': 'var_label', 'V5': 'level_label', 'V3': 'ref_level_indicator'}, inplace=True)
else:
    print("Warning: Data for predictor composition not fully loaded. `comp_top_pred` may not work.")


def comp_top_pred(dhb_name: str, source_df=pred_dhb_perc_full_df):
    if source_df.empty:
        print(f"No data for composition plot for DHB: {dhb_name}")
        return

    plot_data = source_df[
        (source_df['DHB2015_name'] == dhb_name) &
        (source_df['ref_level_indicator'] != "NA") & (source_df['ref_level_indicator'] != "ref") &
        (source_df['var_label'] != "birth weight") & (source_df['var_label'] != "Received disability support") # R script filters on V4
    ].copy()

    plot_data['var_label'] = plot_data['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False)
    plot_data['level_label'] = plot_data['level_label'].str.replace("No qualifications", "No quals", regex=False)
    plot_data['varlevel'] = plot_data['var_label'].fillna('') + ": " + plot_data['level_label'].fillna('')
    plot_data['group'] = np.where(plot_data['perc_diff'] <= 0, 1, 0)

    comp_replacements = {
        "N quarters enrolled GP: 0-3 [(]vs 12[+][)]": "Continuously enrolled with GP \n for 9 months or less",
        "Rented home: Yes": "Living in a rented home",
        "Pacific ethnicity: Yes": "Pacific",
        "Maori ethnicity: Yes": "M\u0101ori", # Unicode for macron
        "European ethnicity: Yes": "European",
        "Asian ethnicity: Yes": "Asian",
        "Mother high qual: No quals [(]vs degree[)]": "Mother no qualifications",
        "N motor vehicles available: 0 [(]vs 2[+][)]": "No Motor Vehicles",
        "Household size: 8[+] [(]vs <5[)]": "8 or more people reside in household",
        "Mother age: <20 [(]vs 30-34[)]": "Mother <20 years at birth",
        "NZDep: Quintile 5 [(]vs 1[)]": "Residing in deprived area (NZDep Q5)"
    }
    for old, new in comp_replacements.items():
        plot_data['varlevel'] = plot_data['varlevel'].str.replace(old, new, regex=False) # Use regex=False

    # R script selects specific rows by index after replacements, this is fragile.
    # It's better to filter by the new 'varlevel' names if possible, or by original var/level.
    # For now, acknowledge this selection happens.
    # Example: plotdata = plotdata[plotdata['varlevel'].isin([...list of selected varlevels...])]
    # R code: plotdata = plotdata[c(5,4,1,29,15,11,16,28,9,20,23),] - this needs careful translation if exact rows are key.
    # This selection logic is very specific and might need the exact state of plot_data before this line.
    # For Python, it's better to select based on content if possible.

    print(f"\n--- Data for Predictor Composition Plot: {dhb_name} ---")
    # print(plot_data[['varlevel', 'perc_diff', 'group']].head())
    print(f"Plotting Predictor Composition for {dhb_name}")
    # --- Matplotlib/Seaborn plotting would go here ---
    # This would be a horizontal bar/point plot (geom_point + hline)
    pass


# --- Characteristic Table Functions ---
pred_dist_ta_df = load_csv_data("pred_dist_ta.csv") # R script uses this name
pred_ta_perc_full_df = pd.DataFrame() # Initialize

if not pred_dist_ta_df.empty and not dhb_map_df.empty and not var_labs_df.empty:
    pred_dist_ta_total = pred_dist_ta_df[
        (pred_dist_ta_df['level'] != "MISSING") & (pred_dist_ta_df['grp_ta_ward_name'] != "")
    ].copy()
    pred_dist_ta_total['COUNT'] = pd.to_numeric(pred_dist_ta_total['COUNT'], errors='coerce')
    pred_dist_ta_total = pred_dist_ta_total.groupby(['grp_ta_ward_name', 'var'])['COUNT'].sum().reset_index().rename(columns={'COUNT': 'var_total'})

    pred_ta_perc = pd.merge(pred_dist_ta_df, pred_dist_ta_total, on=['grp_ta_ward_name', 'var'], how='left')
    pred_ta_perc = pred_ta_perc[ (pred_ta_perc['grp_ta_ward_name'] != "") & pred_ta_perc['level'].notna() & (pred_ta_perc['level'] != "MISSING")].copy()
    pred_ta_perc['COUNT'] = pd.to_numeric(pred_ta_perc['COUNT'], errors='coerce')
    pred_ta_perc['level'] = pred_ta_perc['level'].astype(str)
    pred_ta_perc['perc'] = round(pred_ta_perc['COUNT'] / pred_ta_perc['var_total'] * 100, 0)

    pred_ta_perc = pd.merge(pred_ta_perc, dhb_map_df, left_on="grp_ta_ward_name", right_on="WARD2013_name", how="left")

    var_labs_df_str_levels_ta = var_labs_df.copy()
    var_labs_df_str_levels_ta['V2'] = var_labs_df_str_levels_ta['V2'].astype(str)
    pred_ta_perc_full_df = pd.merge(var_labs_df_str_levels_ta, pred_ta_perc, left_on=['V1', 'V2'], right_on=['var', 'level'], how="right")
    pred_ta_perc_full_df.rename(columns={'V4': 'var_label', 'V5': 'level_label', 'V3': 'ref_level_indicator'}, inplace=True)
else:
    print("Warning: Data for TA characteristic tables not fully loaded.")


def chartable(dhb_name: str, source_df=pred_ta_perc_full_df):
    if source_df.empty:
        print(f"No data for chartable for DHB: {dhb_name}")
        return pd.DataFrame()

    table_data = source_df[
        (source_df['DHB_name'] == dhb_name) &
        (source_df['ref_level_indicator'] != "NA") & (source_df['ref_level_indicator'] != "ref") &
        (source_df['var_label'] != "birth weight")
    ].copy()

    table_data['var_label'] = table_data['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False)
    table_data['level_label'] = table_data['level_label'].str.replace("No qualifications", "No quals", regex=False)
    table_data['varlevel'] = table_data['var_label'].fillna('') + ": " + table_data['level_label'].fillna('')

    # Apply varlevel name replacements (same as comp_top_pred)
    comp_replacements_chart = { # Using a distinct dict in case they diverge
        "N quarters enrolled GP: 0-3 [(]vs 12[+][)]": "Continuously enrolled with GP for 9 months or less",
        "Rented home: Yes": "Living in a rented home",
        "Pacific ethnicity: Yes": "Pacific",
        "Maori ethnicity: Yes": "M\u0101ori",
        "European ethnicity: Yes": "European",
        "Asian ethnicity: Yes": "Asian",
        "Mother high qual: No quals [(]vs degree[)]": "Mother no qualifications",
        "N motor vehicles available: 0 [(]vs 2[+][)]": "No Motor Vehicles",
        "Household size: 8[+] [(]vs <5[)]": "8 or more people reside in household",
        "Mother age: <20 [(]vs 30-34[)]": "Mother <20 years at birth",
        "NZDep: Quintile 5 [(]vs 1[)]": "Residing in deprived area (NZDep Q5)"
    }
    for old, new in comp_replacements_chart.items():
        table_data['varlevel'] = table_data['varlevel'].str.replace(old, new, regex=False)

    # Filter for specific var_label and level (V2 in R) combinations
    # This is complex due to R's OR conditions. Replicating carefully:
    filter_cond = (
        ((table_data['var_label'] == "Mother high qual") & (table_data['V2'] == "0")) | # V2 is original level before rename
        ((table_data['var_label'] == "N motor vehicles available") & (table_data['V2'] == "0")) |
        (table_data['var_label'].isin(["Maori ethnicity", "Pacific ethnicity", "European ethnicity", "Asian ethnicity"])) |
        ((table_data['var_label'] == "NZDep") & (table_data['V2'] == "5")) |
        ((table_data['var_label'] == "Mother age") & (table_data['V2'] == "1")) | # Assuming V2 is numeric for age group
        ((table_data['var_label'] == "Household size") & (table_data['V2'] == "3")) | # Assuming V2 is numeric for size group
        ((table_data['var_label'] == "N quarters enrolled GP") & (table_data['V2'] == "1")) |
        (table_data['var_label'] == "Rented home")
    )
    table_data_filtered = table_data[filter_cond].copy()

    table_data_selected = table_data_filtered[['varlevel', 'grp_ta_ward_name', 'perc']]

    if table_data_selected.empty:
        print(f"No data after filtering for chartable for DHB: {dhb_name}")
        return pd.DataFrame()

    # Reshape: timevar="grp_ta_ward_name", idvar="varlevel", direction="wide"
    # Using pivot_table
    table_wide = table_data_selected.pivot_table(index='varlevel', columns='grp_ta_ward_name', values='perc').reset_index()

    # R script reorders rows by specific indices: table = table[c(3, 2, 1, 11, 6, 5, 7, 10, 4, 8, 9),]
    # This order needs to be explicitly defined if required, e.g., by creating a categorical type for 'varlevel'
    # For now, the Python version will have rows sorted by 'varlevel' alphabetically.

    print(f"Chartable data prepared for DHB: {dhb_name}. Shape: {table_wide.shape}")
    # Actual CSV writing is handled by the calling script (Produce_Outputs.py)
    return table_wide


# --- LB Characteristic Table Functions (similar to chartable but for LBs) ---
lb_map_df = load_csv_data("lb_map.csv")
pred_dist_lb_df = load_csv_data("lb_full_data.csv") # R: lb_full_data.csv, SAS: lb_full_data.csv
pred_lb_perc_full_df = pd.DataFrame() # Initialize

if not pred_dist_lb_df.empty and not lb_map_df.empty and not var_labs_df.empty:
    # Combine "Great Barrier and Waiheke" and "Waitemata" for pred_dist_lb_df
    # This involves grouping and summing, similar to com_all_year_lb processing
    # Simplified for now: assuming pred_dist_lb_df has the combined LB name if needed, or needs pre-processing.
    # The R code does this combination (GBWW) before calculating percentages.
    # For Python, this means the input lb_full_data.csv should ideally have this combined LB.
    # If not, the logic from R to create GBWW by summing components would be needed here.
    # (Assuming 'pred_dist_lb_df' is the equivalent of R's 'pred_dist_lb_new' which has GBWW)

    pred_dist_lb_total = pred_dist_lb_df[
        (pred_dist_lb_df['level'] != "Missing") & (pred_dist_lb_df['CB2018_name'] != "") &
        ~pred_dist_lb_df['CB2018_name'].isin(["Great Barrier and Waiheke", "Waitemata", "Onewhero-Tuakau"]) &
        pred_dist_lb_df['level'].notna()
    ].copy()
    # Ensure 'total' is numeric for sum
    pred_dist_lb_total['total'] = pd.to_numeric(pred_dist_lb_total['total'], errors='coerce')
    pred_dist_lb_total = pred_dist_lb_total.groupby(['CB2018_name', 'var'])['total'].sum().reset_index().rename(columns={'total': 'var_total'})

    pred_lb_perc = pd.merge(pred_dist_lb_df, pred_dist_lb_total, on=['CB2018_name', 'var'], how='left')
    pred_lb_perc = pred_lb_perc[
        (pred_lb_perc['CB2018_name'] != "") &
        ~pred_lb_perc['CB2018_name'].isin(["Great Barrier and Waiheke", "Waitemata", "Onewhero-Tuakau"]) &
        pred_lb_perc['level'].notna() & (pred_lb_perc['level'] != "Missing")
    ].copy()
    pred_lb_perc['total'] = pd.to_numeric(pred_lb_perc['total'], errors='coerce')
    pred_lb_perc['level'] = pred_lb_perc['level'].astype(str)
    pred_lb_perc['perc'] = round(pred_lb_perc['total'] / pred_lb_perc['var_total'] * 100, 0)

    pred_lb_perc = pd.merge(pred_lb_perc, lb_map_df, on="CB2018_name", how="left") # lb_map provides DHB_name for LBs

    var_labs_df_str_levels_lb = var_labs_df.copy()
    var_labs_df_str_levels_lb['V2'] = var_labs_df_str_levels_lb['V2'].astype(str)
    pred_lb_perc_full_df = pd.merge(var_labs_df_str_levels_lb, pred_lb_perc, left_on=['V1', 'V2'], right_on=['var', 'level'], how="right")
    pred_lb_perc_full_df.rename(columns={'V4': 'var_label', 'V5': 'level_label', 'V3': 'ref_level_indicator'}, inplace=True)
else:
    print("Warning: Data for LB characteristic tables not fully loaded.")


def chartable_lb(dhb_name: str, source_df=pred_lb_perc_full_df):
    # This function is very similar to chartable, just uses CB2018_name and filters by DHB_name from lb_map
    if source_df.empty:
        print(f"No data for chartable_lb for DHB: {dhb_name}")
        return pd.DataFrame()

    table_data_lb = source_df[
        (source_df['DHB2015_name'] == dhb_name) & # DHB_name comes from merging with lb_map
        (source_df['ref_level_indicator'] != "NA") & (source_df['ref_level_indicator'] != "ref") &
        (source_df['var_label'] != "birth weight")
    ].copy()

    table_data_lb['var_label'] = table_data_lb['var_label'].str.replace("Mother highest qualification", "Mother high qual", regex=False)
    table_data_lb['level_label'] = table_data_lb['level_label'].str.replace("No qualifications", "No quals", regex=False)
    table_data_lb['varlevel'] = table_data_lb['var_label'].fillna('') + ": " + table_data_lb['level_label'].fillna('')

    comp_replacements_chart_lb = { # Using a distinct dict in case they diverge
        "N quarters enrolled GP: 0-3 [(]vs 12[+][)]": "Continuously enrolled with GP for 9 months or less",
        "Rented home: Yes": "Living in a rented home",
        "Pacific ethnicity: Yes": "Pacific",
        "Maori ethnicity: Yes": "M\u0101ori",
        "European ethnicity: Yes": "European",
        "Asian ethnicity: Yes": "Asian",
        "Mother high qual: No quals [(]vs degree[)]": "Mother no qualifications",
        "N motor vehicles available: 0 [(]vs 2[+][)]": "No Motor Vehicles",
        "Household size: 8[+] [(]vs <5[)]": "8 or more people reside in household",
        "Mother age: <20 [(]vs 30-34[)]": "Mother <20 years at birth",
        "NZDep: Quintile 5 [(]vs 1[)]": "Residing in deprived area (NZDep Q5)"
    }
    for old, new in comp_replacements_chart_lb.items():
        table_data_lb['varlevel'] = table_data_lb['varlevel'].str.replace(old, new, regex=False)

    filter_cond_lb = (
        ((table_data_lb['var_label'] == "Mother high qual") & (table_data_lb['V2'] == "0")) |
        ((table_data_lb['var_label'] == "N motor vehicles available") & (table_data_lb['V2'] == "0")) |
        (table_data_lb['var_label'].isin(["Maori ethnicity", "Pacific ethnicity", "European ethnicity", "Asian ethnicity"])) |
        ((table_data_lb['var_label'] == "NZDep") & (table_data_lb['V2'] == "5")) |
        ((table_data_lb['var_label'] == "Mother age") & (table_data_lb['V2'] == "1")) |
        ((table_data_lb['var_label'] == "Household size") & (table_data_lb['V2'] == "3")) |
        ((table_data_lb['var_label'] == "N quarters enrolled GP") & (table_data_lb['V2'] == "1")) |
        (table_data_lb['var_label'] == "Rented home")
    )
    table_data_lb_filtered = table_data_lb[filter_cond_lb].copy()

    table_data_lb_selected = table_data_lb_filtered[['varlevel', 'CB2018_name', 'perc']]

    if table_data_lb_selected.empty:
        print(f"No data after filtering for chartable_lb for DHB: {dhb_name}")
        return pd.DataFrame()

    table_lb_wide = table_data_lb_selected.pivot_table(index='varlevel', columns='CB2018_name', values='perc').reset_index()

    print(f"Chartable_lb data prepared for DHB: {dhb_name}. Shape: {table_lb_wide.shape}")
    return table_lb_wide


# --- Example Usage (Illustrative) ---
if __name__ == '__main__':
    print("--- Running Data and Functions (Python version) ---")

    # Example calls to test data preparation for plotting functions
    print("\nIllustrative call for myplot_vht (Auckland):")
    myplot_vht("Auckland")

    print("\nIllustrative call for myplot_vht_lb (Auckland):")
    myplot_vht_lb("Auckland")

    print("\nIllustrative call for pred_forest_vht (Auckland):")
    pred_forest_vht("Auckland")

    print("\nIllustrative call for comp_top_pred (Auckland):")
    comp_top_pred("Auckland")

    print("\nIllustrative call for chartable (Bay of Plenty):")
    bop_char_table = chartable("Bay of Plenty")
    # In Produce_Outputs.py, this df would be saved to CSV.
    # print("Bay of Plenty CharTable head:")
    # print(bop_char_table.head())

    print("\nIllustrative call for chartable_lb (Auckland):")
    auckland_char_table_lb = chartable_lb("Auckland")
    # print("Auckland CharTable_LB head:")
    # print(auckland_char_table_lb.head())

    print("\n--- Finished Data and Functions (Python version) ---")

```
