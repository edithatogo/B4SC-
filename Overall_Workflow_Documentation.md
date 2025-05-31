## Overall Workflow Documentation: B4SC Microsimulation Analysis Pipeline

### 1. Introduction
The overall purpose of this set of SAS and R scripts is to conduct a comprehensive analysis of B4 School Check (B4SC) coverage. This involves creating a suitable denominator population, enriching it with a wide array of demographic, socioeconomic, and health-related variables, and then performing statistical analysis to identify key predictors of B4SC non-completion. The pipeline also generates numerous visualizations and summary tables for reporting and dissemination of findings. While not explicitly a microsimulation model in the traditional sense of simulating individual future events, it prepares and analyzes detailed microdata to understand factors influencing B4SC outcomes.

### 2. Data Sources
The initial data processing phase (SAS scripts) relies on various raw data sources, primarily from the Integrated Data Infrastructure (IDI), including but not limited to:
*   **Stats NZ Data:** Resident population (`snz_res_pop`), personal details (`personal_detail`), address information (`address_notification_full`), overseas spells (`person_overseas_spell`).
*   **Ministry of Health (MOH) Data:** B4SC checks (`moh.b4sc`), population cohort demographics (`moh.pop_cohort_demographics`), hospital discharges and events (`moh.pub_fund_hosp_discharges_event`), PHO enrolment (`moh.pho_enrolment`), SOCRATES disability and referral data (`soc.moh_disability`, `soc.moh_referral`).
*   **Department of Internal Affairs (DIA) Data:** Death registrations (`dia_clean.deaths`), birth registrations (`dia_clean.births`).
*   **Census Data:** Individual, household, and dwelling data from 2013 and 2018 Censuses (e.g., `census.census_individual_2013`, `cen_clean.census_individual_2018`).
*   **Metadata/Concordance Files:** Deprivation indices (`metadata.depindex2013`), area concordances (e.g., `Annual Areas 2018.csv`).

### 3. Phase 1: SAS Processing (Data Preparation & Aggregation)
The SAS scripts are responsible for constructing the core analytical dataset by cleaning, linking, and aggregating data from various sources.

*   **General Role:** To create a robust, multi-year dataset of children eligible for B4SC, augmented with numerous predictor variables, and then to produce summary CSV files suitable for statistical analysis in R.
*   **Script Flow and Purpose:**
    1.  **`1. create denominator pop.sas`**:
        *   Creates the initial denominator population of 4-year-old children for specific fiscal years.
        *   Filters resident population, adds birth details, incorporates death information, calculates age, and filters for time spent overseas.
        *   Output: `dlab.denominator_pop_&year._junyr`
    2.  **`2. create b4sc dataset.sas`**:
        *   Takes the denominator population and enriches it with B4SC check data, ethnicity, detailed address history (meshblock, TA, DHB, NZDep), address changes, hospital visit history, GP attendance, detailed Census 2013/2018 data (child, household, parents), birth record details, and disability flags.
        *   Performs extensive variable recoding and derivation.
        *   Output: `dlab2.b4sc_cov_&year._junyr_full`
    3.  **`3. combine years.sas`**:
        *   Appends the yearly datasets (`b4sc_cov_&year._junyr_full` from 2011 to 2018).
        *   Combines census-derived variables from 2013 and 2018 censuses using year-specific logic.
        *   Derives further summary variables.
        *   Output: `dlab2.b4sc_allyr_FINAL`
    4.  **`4. create datalab output files.sas`**:
        *   Takes the combined multi-year dataset.
        *   Uses macros to generate numerous aggregated summary datasets (non-completion rates, completion rates, predictor distributions) stratified by various demographic and geographic factors (DHB, TA/Ward, Local Board, national).
        *   Calculates missing value counts.
        *   Outputs these summaries as CSV files.

*   **Key CSV Outputs for R Processing:**
    *   `dhb_full_data.csv` (Non-completion rates by predictors, by DHB)
    *   `taward_final.csv` (Non-completion rates by predictors, by TA/Ward - uses `grp_ta_ward_name`) - *Note: The SAS script also creates an ungrouped version earlier.*
    *   `completion_all_year.csv` (National completion rates by year)
    *   `completion_all_year_ta.csv` (Completion rates by grouped TA/Ward and year)
    *   `national_incomplete.csv` (National non-completion rates by predictors)
    *   `missing_count.csv` (Missing value counts for predictors)
    *   `pred_dist_DHB.csv` (Predictor distributions by DHB)
    *   `pred_dist_TA.csv` (Predictor distributions by grouped TA/Ward)
    *   `lb_full_data.csv` (Non-completion rates by predictors, by Auckland Local Board)
    *   `completion_all_year_LB.csv` (Completion rates by Auckland Local Board and year)
    *   `grp_taward_final.csv` (Used in `Analysis_Predictor_Rank.R`, likely similar to `taward_final.csv` but specifically for grouped TAs if distinct) - *Note: The SAS script for `4. create datalab output files.sas` produces `taward_final.csv` which seems to be based on `grp_ta_ward_name` in its final version.*

### 4. Phase 2: R Processing (Analysis & Visualization)
The R scripts take the summary CSV files generated by SAS and perform further analysis, calculate relative risks, rank predictors, and generate a wide range of visualizations.

*   **General Role:** To conduct statistical analysis on the prepared data, identify key drivers of B4SC non-completion, and produce visual and tabular outputs for reporting.
*   **Script Flow and Dependencies:**
    1.  **`Data_and_Functions.R`**:
        *   Acts as a setup script.
        *   Loads many of the key CSV summary files output by SAS.
        *   Performs initial data manipulations: merges TA data with DHB maps, calculates completion rates from counts, calculates Relative Risks (RRs) and Confidence Intervals (CIs) for predictors of non-completion (specifically for `dhb_incomplete` data to create `allplotdata`).
        *   Defines a large suite of core, reusable functions for creating various plot types (`ggplot2` line plots for attendance, forest plots for RRs, bar plots for predictor composition) and some summary tables (`chartable`, `chartable_lb`).
        *   Defines color palettes and standard plot themes.
    2.  **`Analysis_Predictor_Rank.R`**:
        *   Loads specific SAS outputs like `national_incomplete.csv`, `list of var levels.csv`, `grp_taward_final.csv`, and `dhb_map.csv`.
        *   It also uses `dhb_incomplete_ref_ci` which is either loaded from a CSV not explicitly listed (but generated by a process similar to `Data_and_Functions.R`) or it assumes `Data_and_Functions.R` has been run and this object is in the environment. Given the context, it's likely that `Data_and_Functions.R` prepares this object.
        *   Calculates RRs and CIs for non-completion at national, DHB, and TA/Ward levels.
        *   Ranks predictors based on RR for VHT, Nurse, and SDQT modules.
        *   Identifies and outputs CSV files for the top 10 predictors at DHB and TA/Ward levels (e.g., `top10_vht_dhb.csv`, `top10_vht_ta.csv`).
    3.  **`Produce_Outputs.R`**:
        *   Acts as an execution script that calls functions defined in `Data_and_Functions.R`.
        *   It iterates through each DHB (and Auckland Local Boards) to generate a standardized set of plots and tables.
        *   Outputs include numerous PNG files for forest plots, attendance rate line plots, and predictor composition plots.
        *   It also calls `chartable()` and `chartable_lb()` from `Data_and_Functions.R`, which directly write CSV summary tables (e.g., `AucklandCharTable.csv`).

### 5. Overall Data Flow Diagram (Text-based)

```
[Raw Databases (IDI, MOH, Census, Stats NZ, etc.)]
              |
              V
[SAS Script: 1. create denominator pop.sas] -----------------> dlab.denominator_pop_&year._junyr
              |
              V
[SAS Script: 2. create b4sc dataset.sas] --------------------> dlab2.b4sc_cov_&year._junyr_full
              |
              V
[SAS Script: 3. combine years.sas] --------------------------> dlab2.b4sc_allyr_FINAL
              |
              V
[SAS Script: 4. create datalab output files.sas] ----------> [Multiple Summary CSVs:
                                                                - national_incomplete.csv
                                                                - dhb_fulldata.csv
                                                                - taward_final.csv (grouped)
                                                                - completion_all_year.csv
                                                                - completion_all_year_ta.csv
                                                                - pred_dist_DHB.csv
                                                                - pred_dist_TA.csv
                                                                - missing_count.csv
                                                                - lb_full_data.csv
                                                                - completion_all_year_LB.csv
                                                                - etc. ]
                                                                  |
                                                                  | (These CSVs are the primary inputs for R)
                                                                  V
[R Script: Data_and_Functions.R] ---------------------------> (Loads many of the above CSVs)
(Defines functions, prepares data objects like `allplotdata`)     |   (Prepares data like `national_incomplete_ref_ci`,
                                                                  |    `dhb_incomplete_ref_ci` used by Predictor_Rank)
                                                                  |      \
                                                                  |       \
                                                                  V        V
                                          [R Script: Analysis_Predictor_Rank.R] --> [Analysis CSVs:
                                          (Uses data from Data_and_Functions.R or        - top10_vht_dhb.csv
                                           direct CSVs e.g. national_incomplete.csv)      - top10_nurse_freq.csv
                                                                                          - top10_sdqt_dhb.csv
                                                                                          - top10_vht_ta.csv
                                                                                          - DHB_ta.csv ]
                                                                  |
                                                                  V
[R Script: Produce_Outputs.R] --------------------------------> [Output Files:
(Uses functions and data objects from Data_and_Functions.R)       - Numerous PNG Plots (Forest, Line, Composition)
                                                                  - CSV Characteristic Tables (DHB & LB specific) ]
```

### 6. Key Outputs of the Entire Process
The entire pipeline results in a rich set of outputs for understanding B4SC coverage:

*   **Documented Code:** This set of documentation for each SAS and R script, plus this overall workflow document.
*   **Core Analytical Dataset:** `dlab2.b4sc_allyr_FINAL` (SAS dataset, though not directly used by end-users, it's the master file before SAS aggregation).
*   **Aggregated CSV Datasets (from SAS):** A suite of CSV files summarizing various aspects of B4SC checks, non-completion rates, and predictor distributions at different geographical levels. These are key inputs for the R-based analysis.
*   **Predictor Ranking CSVs (from R):** Specific CSV files identifying the top 10 predictors of non-completion for different modules and geographical levels.
*   **Visualizations (PNG Plots from R):** A large collection of plots including:
    *   Forest plots showing Relative Risks of non-completion for various predictors.
    *   Line plots showing trends in B4SC attendance rates over time by TA/Ward and Local Board.
    *   Bar plots comparing predictor compositions within DHBs to national averages.
*   **Characteristic Summary Tables (CSV from R):** Tables summarizing predictor distributions within DHBs and Auckland Local Boards.

This multi-stage process transforms raw administrative and survey data into actionable insights regarding B4SC coverage and its determinants.
---
