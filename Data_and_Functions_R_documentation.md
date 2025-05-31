## R Script Documentation: Data_and_Functions.R

### 1. Overall Purpose
This R script serves as a foundational component for a larger analysis project, likely related to B4 School Check (B4SC) coverage. Its primary purposes are:
1.  **Data Loading:** To read various pre-processed CSV data files containing B4SC completion rates, predictor distributions, and geographic mapping information.
2.  **Data Preparation & Manipulation:** To perform initial data merging (e.g., mapping Territorial Authorities to DHBs), calculate rates (completion rates), calculate relative risks (RR) and confidence intervals (CI) for predictors of non-completion, and clean/reshape data into formats suitable for analysis and plotting.
3.  **Function Definition:** To define a suite of reusable R functions for generating specific visualizations (line plots, forest plots, bar charts using `ggplot2`) and summary tables. These functions encapsulate the logic for creating consistent outputs for different DHBs or modules.
4.  **Aesthetic Definitions:** To define standard color palettes and `ggplot2` theme elements to ensure consistency in visualizations.

The script prepares data and creates tools (functions) that are likely utilized by other scripts in the project (e.g., an `Produce_Outputs.R` script) to generate final analytical outputs like reports or individual plot files.

### 2. Input Datasets/Sources
The script reads the following CSV files:

*   `dhb_map.csv`: A concordance table mapping Territorial Authorities (WARDS) to District Health Boards (DHBs).
*   `list of var levels.csv`: Contains labels and reference group information for predictor variables and their levels. Loaded into `varlabs`.
*   `completion_all_year.csv`: National level B4SC completion counts by module and year. Loaded into `com_all_year`.
*   `completion_all_year_ta.csv`: TA (Territorial Authority/Ward) level B4SC completion counts by module and year. Loaded into `com_all_year_ta`.
*   `completion_all_year_LB.csv`: Local Board level B4SC completion counts for Auckland DHBs by module and year. Loaded into `com_all_year_lb`.
*   `dhb_fulldata.csv`: DHB level data on B4SC non-completion counts stratified by various predictors. Loaded into `dhb_incomplete`.
*   `missing_count.csv`: National level counts of missing and non-missing values for predictors. Loaded into `pred`.
*   `pred_dist_dhb.csv`: Distribution of predictor variables at the DHB level.
*   `pred_dist_ta.csv`: Distribution of predictor variables at the TA (Territorial Authority/Ward) level.
*   `lb_map.csv`: A concordance table for Local Boards (though its direct usage after loading isn't explicitly shown in `chartable_lb`'s initial data prep, `pred_lb_perc` uses it).
*   `lb_full_data.csv`: Local Board level data, likely similar to `dhb_fulldata.csv` but for Auckland Local Boards. Loaded into `pred_dist_lb`.


### 3. Output Dataset(s)/Effects
This script primarily defines functions and creates data objects in the R environment for use by other scripts. It does not, for the most part, directly output files, with the specific exception of:

*   The `chartable(dhb)` function writes a CSV file named `paste0(dhb, "CharTable", ".csv")`.
*   The `chartable_lb(DHB)` function writes a CSV file named `paste0(DHB, "CharTable_LB", ".csv")`.

The main "outputs" are the R functions themselves and the processed data frames (e.g., `com_all_year_final`, `allplotdata`, `pred_dhb_perc_full`) that are ready for plotting or further analysis. The example calls to plotting functions (e.g., `myplot_vht("Auckland")`) will generate plots in the R session if run interactively but are often commented out for explicit file saving in a separate output script.

### 4. Major Processing Steps/Function Categories

1.  **Data Loading and Initial Merging:**
    *   Reads multiple CSV files using `read.csv()`.
    *   Merges TA-level data with DHB mapping information using `left_join(com_all_year_ta, dhb_map, ...)`.
    *   Merges predictor data with variable/level labels from `varlabs` using `left_join()`.
    *   Combines national average rows with TA-level and Local Board-level data to include a reference line in plots.
    *   Specific data aggregation for Auckland Local Boards: combines "Great Barrier and Waiheke" with "Waitemata" into a new category "Great Barrier, Waiheke and Waitemata".

2.  **Calculation of Rates:**
    *   Calculates B4SC completion rates (e.g., `vht_rate = vht_complete / total`) for national, TA, and Local Board levels.
    *   Converts rates to percentages (e.g., `vht_rate_perc = round(vht_rate*100,2)`).

3.  **Calculation of Relative Risks (RR) and Confidence Intervals (CI):**
    *   For the `dhb_incomplete_ref_ci` dataset, it calculates:
        *   Relative Risks (`rr_vht`, `rr_nurse`, `rr_sdqt`) for non-completion for each predictor level compared to a defined reference level within each DHB.
        *   Standard errors and 95% Confidence Intervals (`vht_ci_ll`, `vht_ci_ul`, etc.) for these RRs.

4.  **Data Cleaning and Reshaping for Plotting & Tables:**
    *   **Renaming and Labeling:** Uses `str_replace` and `str_replace_all` extensively to shorten labels for predictor variables and levels to make them more suitable for plots (e.g., "Mother highest qualification" to "Mother high qual").
    *   **Factor Level Ordering:** Explicitly orders factor levels for `grp_ta_ward_name`, `CB2018_name`, and `varlevelnew` to control the order of appearance in legends and on plot axes (e.g., ensuring "National average" appears first or specific predictors are grouped logically).
    *   **Creating Combined Variables:** Creates `varlevel` by pasting variable labels and level labels (e.g., "NZDep: Quintile 5").
    *   **Filtering:** Subsets data for specific DHBs or removes rows with missing/irrelevant data (e.g., `filter(V3 == "")` to exclude reference levels from RR plots, `filter(var != "los_days_grp")`).
    *   **Reshaping for Tables:** Uses `reshape()` within `chartable` and `chartable_lb` functions to transform long-format data (one row per TA/LB per variable level) into a wide format suitable for a summary table (variables as rows, TAs/LBs as columns).

5.  **Defining Color Palettes and Themes for `ggplot2`:**
    *   Defines a custom color vector `col` for use in plots.
    *   Plotting functions consistently use `theme_classic()` or `theme_bw()` as a base and then customize elements like legend position, grid lines, text sizes, and strip background colors for faceted plots.

### 5. Key Functions Defined

*   **`myplot_vht(dhb)`, `myplot_nurse(dhb)`, `myplot_sdqt(dhb)`:**
    *   **Purpose:** To generate line plots of B4SC attendance rates (VHT, Nurse, SDQT respectively) over years for different Territorial Authorities/Wards within a specified `dhb`. Includes a "National average" line.
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** A `ggplot` object representing the line plot.

*   **`myplot_vht_lb(dhb)`, `myplot_nurse_lb(dhb)`, `myplot_sdqt_lb(dhb)`:**
    *   **Purpose:** Similar to above, but plots attendance rates for Auckland Local Boards (`CB2018_name`) within the specified Auckland `dhb`. Includes specific logic for y-axis limits based on the DHB.
    *   **Parameters:** `dhb` (character string: name of an Auckland DHB).
    *   **Returns/Generates:** A `ggplot` object.

*   **`pred_forest_vht(dhb)`, `pred_forest_nurse(dhb)`, `pred_forest_sdqt(dhb)`:**
    *   **Purpose:** To generate forest plots displaying Relative Risks (RRs) and 95% Confidence Intervals for B4SC non-completion (VHT, Nurse, SDQT respectively) associated with various predictor variables, for a specified `dhb`. Predictors are grouped into categories ("Family Socioeconomic Position", "Family & Child Characteristics", "Health & Health System").
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** A `gtable` object (a modified `ggplot` object) representing the forest plot. Includes dynamic upper limits for the x-axis based on the DHB and custom styling for facet strips.

*   **`comp_top_pred(dhb)`:**
    *   **Purpose:** To create a bar plot (actually a point plot that looks like a lollipop chart) showing the percentage point difference of selected predictor level distributions within a specified `dhb` compared to the national average.
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** A `ggplot` object.

*   **`chartable(dhb)`:**
    *   **Purpose:** To create a summary table of predictor distributions (percentages) for selected variables, with Territorial Authorities/Wards within the specified `dhb` as columns.
    *   **Parameters:** `dhb` (character string: name of the DHB).
    *   **Returns/Generates:** Writes a CSV file named `[dhb_name]CharTable.csv`. The function itself returns the result of `write.csv`.

*   **`chartable_lb(DHB)`:**
    *   **Purpose:** Similar to `chartable`, but creates a summary table for Auckland Local Boards within the specified Auckland `DHB`.
    *   **Parameters:** `DHB` (character string: name of an Auckland DHB).
    *   **Returns/Generates:** Writes a CSV file named `[DHB_name]CharTable_LB.csv`. The function itself returns the result of `write.csv`.

### 6. Libraries Used
The script loads the following R packages:

*   `data.table`
*   `ggplot2`
*   `ggpubr`
*   `tidyverse` (which includes `dplyr`, `tidyr`, `stringr`, etc.)
*   `forestplot` (though its direct functions like `forestplot()` are not used; `ggplot2` is used to create forest plot aesthetics)
*   `lattice`
*   `grid` (used for `gtable` manipulations in forest plots)

---
*Documentation generated by AI agent.*
