## SAS Script Documentation: 4. create datalab output files.sas

### 1. Overall Purpose
This SAS script is designed to generate a series of aggregated summary datasets from the final combined B4 School Check (B4SC) data (`dlab.b4sc_allyr_final`). It uses a set of macros to repeatedly apply `PROC SUMMARY` or `PROC FREQ` to calculate non-completion rates, completion rates, and predictor distributions across various demographic and geographic stratifiers (DHB, TA/Ward, Local Board, national). The script also calculates missing value counts for predictors. The ultimate goal is to export these summarized datasets into multiple CSV files, presumably for use in further analysis, reporting, or visualization by the DataLab users.

### 2. Input Datasets/Sources
*   **`dlab.b4sc_allyr_final`**: The primary input dataset, which is the combined and processed B4SC data from the previous step. Loaded into `work.b4sc`.
*   **`'/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage/Annual Areas 2018.csv'`**: Imported into `work.map`. This file is used to map meshblock data to Local Board names (`CB2018_name`) for Auckland-specific summaries.

### 3. Output Dataset(s)
The script exports the following CSV files to the `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage/` directory:

*   `dhb_full_data.csv`: Non-completion rates by various predictors, stratified by DHB. (Generated twice in the script, the second one overwrites the first, including more predictors like `child_nz_born`, `mother_no_english`, `mother_nz_born`).
*   `taward_final.csv`: Non-completion rates by various predictors, stratified by TA/Ward (ungrouped, then later by `grp_ta_ward_name`). Includes zero-count rows.
*   `completion_all_year.csv`: National B4SC component completion rates (VHT, Nurse, SDQT) by year.
*   `completion_all_year_ta.csv`: B4SC component completion rates (VHT, Nurse, SDQT) by grouped TA/Ward (`grp_ta_ward_name`) and year.
*   `national_incomplete.csv`: National non-completion rates by various predictors.
*   `missing_count.csv`: Counts of missing and non-missing values for various predictors.
*   `pred_dist_DHB.csv`: Distribution (counts) of various predictors, stratified by DHB.
*   `pred_dist_TA.csv`: Distribution (counts) of various predictors, stratified by grouped TA/Ward (`grp_ta_ward_name`).
*   `lb_full_data.csv`: Non-completion rates by various predictors, stratified by Auckland Local Board (`CB2018_name`). Values < 6 are suppressed (set to missing).
*   `completion_all_year_LB.csv`: B4SC component completion rates (VHT, Nurse, SDQT) by Auckland Local Board (`CB2018_name`) and year.

### 4. Major Processing Steps

1.  **Initial Data Load:** Loads `dlab.b4sc_allyr_final` into `work.b4sc`.

2.  **Summarization using Macros:** The script heavily relies on macros to perform repeated summarizations.
    *   **`%dhb(var)` Macro (used twice):**
        *   Summarizes `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete` using `PROC SUMMARY NWAY`.
        *   Classes: `dhb2015_name` and the predictor passed in `&var`.
        *   Output: Dataset named `&var` containing `total` count and sums of incompletes, with added columns `var` (name of the predictor) and `level` (value of the predictor).
        *   These individual predictor summaries are then stacked to create `dhb_full_data`.
    *   **`%dhb(var)` Macro (for `taward_full_data`):**
        *   Similar to the above, but classes are `ta_ward_name` and `&var`.
        *   Output: Stacked into `taward_full_data`.
    *   **Zero-Count Row Generation (for `taward_final`):**
        *   Creates a distinct list of all `var` and `level` combinations from `dhb_full_data` (which is assumed to have all levels).
        *   Creates a distinct list of `ta_ward_name` from `taward_full_data`.
        *   Performs a cross-join (`PROC SQL`) to create `taward_varlist` containing all possible `ta_ward_name` by `var` by `level` combinations.
        *   Filters out some variables not needed for TA/Ward analysis.
        *   Left-joins this complete list back to `taward_full_data` to produce `taward_final`, ensuring rows with zero counts (which would be missing after `PROC SUMMARY`) are included with missing values for summed variables. This is critical for consistent reporting and applying suppression rules.
    *   **`%NA(year)` Macro:**
        *   Summarizes `vht_complete`, `nurse_complete`, `sdqt_complete` using `PROC SUMMARY NWAY` for a given `&year`.
        *   No class statement (national level).
        *   Output: Dataset `year_&year` with `total` count and sums of completes, and an added `YEAR` column.
        *   These are stacked into `completion_all_year`.
    *   **`%TA(year)` Macro (for `completion_all_year_ta`):**
        *   Summarizes `vht_complete`, `nurse_complete`, `sdqt_complete` using `PROC SUMMARY NWAY` for a given `&year`.
        *   Class: `grp_ta_ward_name`.
        *   Output: Stacked into `completion_all_year_ta`.
    *   **`%nation(var)` Macro:**
        *   Summarizes `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete` using `PROC SUMMARY NWAY`.
        *   Class: Predictor passed in `&var`.
        *   Output: Stacked into `national_incomplete`.
    *   **`%TA(var)` Macro (for `taward_full_data` for grouped TAs):**
        *   Similar to `%dhb(var)` but classes are `grp_ta_ward_name` and `&var`. Used to create predictor-based summaries for grouped TAs, which are then processed with the zero-count row generation logic to create the final `taward_final` (this seems to redefine `taward_final` and `dhb_full_data` based on grouped TAs and more predictors).
    *   **`%MISSING(var)` Macro:**
        *   Takes output from `PROC FREQ ... / MISSING OUT=&var;`.
        *   Adds a `var` column (name of the predictor) and renames the predictor column to `level`.
        *   Used to create `missing_count`.
    *   **`%DHBpred(var)` Macro:**
        *   Uses `PROC FREQ` with `TABLE DHB2015_name * &var / ... MISSING OUT=&var;` to get counts for each level of `&var` within each DHB.
        *   Adds `var` and `level` columns.
        *   Output: Stacked into `pred_dist_DHB`.
    *   **`%TApred(var)` Macro:**
        *   Uses `PROC FREQ` with `TABLE grp_ta_ward_name * &var / ... MISSING OUT=&var;` to get counts for each level of `&var` within each grouped TA/Ward.
        *   Adds `var` and `level` columns.
        *   Output: Stacked into `pred_dist_TA`.

3.  **Local Board Specific Summaries (Auckland DHBs):**
    *   Imports `Annual Areas 2018.csv` into `work.map`.
    *   Joins `B4SC_ALLYR_FINAL` with `map` on `mb18_num = MB2018_code` to get `TA2018_name` and `CB2018_name` (Local Board name).
    *   Filters this dataset for Auckland DHBs ("Auckland", "Counties Manukau", "Waitemata") into `dataset2`.
    *   **`%LB(year)` Macro:**
        *   Summarizes `vht_complete`, `nurse_complete`, `sdqt_complete` by `CB2018_name` for a given `&year` from `dataset2`.
        *   Output: Stacked into `completion_all_year_LB`.
    *   **`%LB_inc(var)` Macro:**
        *   Summarizes `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete` by `CB2018_name` and `&var` from `dataset2`.
        *   Output: Stacked into `lb_full_data0`.
    *   **Small Number Suppression for `lb_full_data`:**
        *   The stacked `lb_full_data0` is processed into `lb_full_data`.
        *   An array `CHANGE` iterates through `total`, `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete`. If any of these values are less than 6, they are set to missing (.). This is a common method for data suppression to protect confidentiality.

4.  **Exporting Datasets:** Each of the final summary datasets is exported to a CSV file using `PROC EXPORT`.

### 5. Key Variables Created/Used
Many variables from `b4sc_allyr_final` are used as classification variables in `PROC SUMMARY` or `PROC FREQ`.

**Key variables created within the summarization/macro steps:**
*   **`total`**: Typically represents `_FREQ_` from `PROC SUMMARY` or `COUNT` from `PROC FREQ`, indicating the total number of children in a given stratum.
*   **`vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete`**: These are often sums produced by `PROC SUMMARY`, representing the count of children with incomplete checks for the respective components within a stratum. (Similarly for `vht_complete`, etc.)
*   **`var`**: A character variable added in many macros to hold the name of the predictor variable being summarized (e.g., "nzdep_quint", "sex"). This helps in stacking datasets.
*   **`level`**: A variable added in many macros to hold the specific value/level of the predictor variable in that row (e.g., 1, "Maori", "Female").
*   **`YEAR`**: Added in macros like `%NA` to specify the year for yearly summaries.
*   **`CB2018_name`**: Community Board / Local Board name, added by joining with the `map` dataset.

The original predictor variables (e.g., `n_mv_access`, `low_bw`, `sex`, `maori_eth`, `nzdep_quint`) are used extensively as `CLASS` variables in `PROC SUMMARY` or as table variables in `PROC FREQ`.

### 6. Macro Usage

*   **`%dhb(var)` (used multiple times for DHB and TA/Ward summaries)**
    *   **Parameter:** `var` (name of the predictor variable).
    *   **Action:** `PROC SUMMARY NWAY` calculating sum of `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete`, and `total` count.
    *   **Classes:** `dhb2015_name` (or `ta_ward_name` or `grp_ta_ward_name`) and `&var`.
    *   **Output Structure:** Dataset named `&var` with columns for class variables, `total`, summed incompletes, and new columns `var` (containing "var_name") and `level` (containing the value of `&var`).

*   **`%NA(year)`**
    *   **Parameter:** `year`.
    *   **Action:** `PROC SUMMARY NWAY` calculating sum of `vht_complete`, `nurse_complete`, `sdqt_complete`, and `total` count for a given `&year`.
    *   **Classes:** None (national level).
    *   **Output Structure:** Dataset `year_&year` with `total`, summed completes, and a `YEAR` column.

*   **`%TA(year)` (for yearly completion by TA)**
    *   **Parameter:** `year`.
    *   **Action:** `PROC SUMMARY NWAY` calculating sum of `vht_complete`, `nurse_complete`, `sdqt_complete`, and `total` count for a given `&year`.
    *   **Classes:** `grp_ta_ward_name`.
    *   **Output Structure:** Dataset `year_&year` with `grp_ta_ward_name`, `total`, summed completes, and a `YEAR` column.

*   **`%nation(var)`**
    *   **Parameter:** `var` (name of the predictor variable).
    *   **Action:** `PROC SUMMARY NWAY` calculating sum of `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete`, and `total` count.
    *   **Classes:** `&var`.
    *   **Output Structure:** Dataset `&var` with `total`, summed incompletes, and new columns `var` and `level`.

*   **`%MISSING(var)`**
    *   **Parameter:** `var` (name of the predictor variable for which `PROC FREQ / MISSING OUT=` was run).
    *   **Action:** Data step processing the output of `PROC FREQ`.
    *   **Output Structure:** Modifies the input dataset (named `&var`) by adding a `var` column (containing "var_name") and renaming the original `&var` column (which holds levels) to `level`.

*   **`%DHBpred(var)`**
    *   **Parameter:** `var` (name of the predictor variable).
    *   **Action:** `PROC FREQ` generating counts of `&var` within each `DHB2015_name`.
    *   **Output Structure:** Dataset `&var` with `DHB2015_name`, `COUNT`, and new columns `var` and `level`. Drops `PERCENT`.

*   **`%TApred(var)`**
    *   **Parameter:** `var` (name of the predictor variable).
    *   **Action:** `PROC FREQ` generating counts of `&var` within each `grp_ta_ward_name`.
    *   **Output Structure:** Dataset `&var` with `grp_ta_ward_name`, `COUNT`, and new columns `var` and `level`. Drops `PERCENT`.

*   **`%LB(year)`**
    *   **Parameter:** `year`.
    *   **Action:** `PROC SUMMARY NWAY` on `dataset2` (Auckland DHBs only) calculating sum of `vht_complete`, `nurse_complete`, `sdqt_complete`, and `total` count for a given `&year`.
    *   **Classes:** `CB2018_name` (Local Board).
    *   **Output Structure:** Dataset `year_&year` with `CB2018_name`, `total`, summed completes, and a `YEAR` column.

*   **`%LB_inc(var)`**
    *   **Parameter:** `var` (name of the predictor variable).
    *   **Action:** `PROC SUMMARY NWAY` on `dataset2` (Auckland DHBs only) calculating sum of `vht_incomplete`, `nurse_incomplete`, `sdqt_incomplete`, and `total` count.
    *   **Classes:** `CB2018_name` (Local Board) and `&var`.
    *   **Output Structure:** Dataset `&var` with class variables, `total`, summed incompletes, and new columns `var` and `level`.

---
*Documentation generated by AI agent.*
