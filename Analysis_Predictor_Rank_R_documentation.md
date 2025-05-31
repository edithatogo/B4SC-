## R Script Documentation: Analysis_Predictor_Rank.R

### 1. Overall Purpose
This R script is focused on identifying and ranking the most significant predictors of non-completion for different modules of the B4 School Check (B4SC) – specifically VHT (Vision Hearing Technicians), Nurse-led checks, and SDQT (Strengths and Difficulties Questionnaire - Teacher). The analysis calculates Relative Risks (RRs) for various predictor variables and ranks them to determine the top 10 predictors at national, District Health Board (DHB), and Territorial Authority/Ward (TA/Ward) levels. This helps in understanding which factors are most strongly associated with B4SC non-completion across different geographical granularities.

### 2. Input Datasets/Sources
The script reads the following CSV files:

*   **`national_incomplete.csv`**: Contains national-level data on B4SC non-completion counts, stratified by various predictors.
*   **`list of var levels.csv`**: A supplementary file providing labels and reference group information for predictor variables and their levels. Loaded into `varlabs`.
*   **`dhb_fulldata.csv` (implied)**: While not directly read in this script, the object `dhb_incomplete_ref_ci` is used extensively. Its preparation (calculating RRs and CIs for DHB-level data) is assumed to be similar to how `national_incomplete_ref_ci` is created at the beginning of this script, likely using `dhb_fulldata.csv` as a base.
*   **`grp_taward_final.csv`**: Contains TA/Ward level data on B4SC non-completion counts, stratified by predictors. Loaded into `ta_incomplete`.
*   **`dhb_map.csv`**: A concordance table used to map TA/Wards to DHBs.

### 3. Output Dataset(s)
The script explicitly writes the following CSV files:

*   **`top10_vht_dhb.csv`**: A list of data frames, where each data frame contains the top 10 VHT non-completion predictors for a specific DHB.
*   **`top10_nurse_freq.csv`**: *Correction:* The script has `write.csv(top10_nurse_dhb, "top10_nurse_freq.csv")`. `top10_nurse_dhb` is a list of data frames similar to `top10_vht_dhb` but for the Nurse module. The name "freq" might be a misnomer or intended for a later aggregation step not shown.
*   **`top10_sdqt_dhb.csv`**: A list of data frames, similar to above, but for the SDQT module.
*   **`top10_vht_ta.csv`**: A list of data frames, where each data frame contains the top 10 VHT non-completion predictors for a specific TA/Ward.
*   **`DHB_ta.csv`**: A list of data frames, where each data frame shows the most frequent top 10 VHT predictors identified at the TA/Ward level, summarized for each DHB.

The script also generates several data frames in the R environment as intermediate steps or for direct inspection (e.g., `top10_pred_vht_nation`, frequency tables for top predictors across DHBs printed to console).

### 4. Major Processing Steps

1.  **National Level Analysis:**
    *   Loads `national_incomplete.csv` and `list of var levels.csv`.
    *   Merges data with variable labels and reference group information.
    *   Calculates Relative Risks (RR) and 95% Confidence Intervals (CI) for B4SC non-completion for each predictor level against its defined reference group.
    *   Filters out specific predictors (`bw_grp`, `los_days_grp`).
    *   Ranks predictors based on their RR values for each module (VHT, Nurse, SDQT) and identifies the top 10 nationally.
    *   Performs an exploratory analysis by categorizing predictors ("Family Socioeconomic Position", "Family & Child Characteristics", "Health & Health System") and examining the top-ranked predictors within these categories at the national level.

2.  **DHB Level Analysis:**
    *   Uses the `dhb_incomplete_ref_ci` data frame (assumed to be pre-calculated with RRs and CIs for DHB-level data, similar to the national level).
    *   Filters out `bw_grp` and `los_days_grp`.
    *   Defines functions: `fint_top10_dhb_vht`, `fint_top10_dhb_nurse`, `fint_top10_dhb_sdqt` to identify the top 10 predictors for each module within a specified DHB.
    *   Applies these functions to all DHBs using `lapply`.
    *   Aggregates the results from all DHBs to determine the most frequently occurring top 10 predictors across different DHBs for each module (results printed to console and full lists saved to CSV).

3.  **TA/Ward Level Analysis (Primarily for VHT module shown):**
    *   Loads `grp_taward_final.csv` (TA/Ward level non-completion data) and `dhb_map.csv`.
    *   Merges data with DHB names and variable labels.
    *   Calculates RRs and CIs for B4SC non-completion at the TA/Ward level.
    *   Filters out `bw_grp` and `los_days_grp`.
    *   Defines `find_top10_ta_vht(ta)` to identify the top 10 VHT predictors for a specified TA/Ward.
    *   Applies this function to all TA/Wards (excluding Chatham Islands Territory).
    *   Defines `ta_DHB_top10_vht(dhb)` to summarize, for each DHB, the most frequent top 10 VHT predictors identified among its constituent TA/Wards.
    *   Applies this function to all DHBs.

4.  **Exploratory Analysis for Plot Scaling:**
    *   Defines a function `findmaxrr(dhb)` that takes DHB-level RR and CI data (`allplotdata` - likely a result from `Data_and_Functions.R` or a similar preparation) and prints the maximum RR and CI upper limit values for VHT, Nurse, and SDQT modules. This is likely used to inform axis scaling for visualizations created in other scripts.

### 5. Key Functions Defined

*   **`fint_top10_dhb_vht(dhb)`, `fint_top10_dhb_nurse(dhb)`, `fint_top10_dhb_sdqt(dhb)`:**
    *   **Purpose:** To identify and rank the top 10 predictors of non-completion for the VHT, Nurse, or SDQT module, respectively, within a specific District Health Board (`dhb`).
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** A data frame containing the top 10 predictors (variable label, level label, and RR value) for the specified module and DHB, ordered by descending RR.

*   **`find_top10_ta_vht(ta)`:**
    *   **Purpose:** To identify and rank the top 10 predictors of VHT non-completion within a specific Territorial Authority/Ward (`ta`).
    *   **Parameters:** `ta` (character string: name of the TA/Ward).
    *   **Returns/Generates:** A data frame containing the top 10 VHT predictors (variable label, level label, RR value, DHB name, TA/Ward name) for the specified TA/Ward, ordered by descending RR.

*   **`ta_DHB_top10_vht(dhb)`:**
    *   **Purpose:** To summarize the top 10 VHT non-completion predictors that appear most frequently at the TA/Ward level within a given DHB. It aggregates findings from `find_top10_ta_vht`.
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** A data frame showing the frequency of each predictor appearing in the top 10 list for TAs within that DHB, ordered by frequency.

*   **`findmaxrr(dhb)`:**
    *   **Purpose:** An exploratory function to determine the maximum Relative Risk (RR) and upper Confidence Interval (CI) values for VHT, Nurse, and SDQT non-completion within a specific DHB. This information is likely used to set consistent y-axis limits for plots generated in other scripts.
    *   **Parameters:** `dhb` (character string: name of the DHB). The function expects `allplotdata` (likely from `Data_and_Functions.R`) to be available in the global environment.
    *   **Returns/Generates:** Prints the maximum RR and CI values to the console.

### 6. Libraries Used
The script does not explicitly load libraries using `library()` calls. However, it heavily uses functions typically associated with the `tidyverse` suite of packages, especially:
*   **`dplyr`**: Functions like `left_join`, `rename`, `mutate`, `filter`, `select`, `group_by`, `summarise`, `arrange`.
*   **`stringr`**: Functions like `str_replace`.

It's assumed that these packages (or the umbrella `tidyverse` package) are loaded in the R session before this script is run.

---
*Documentation generated by AI agent.*
