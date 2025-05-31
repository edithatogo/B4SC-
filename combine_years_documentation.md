## SAS Script Documentation: 3. combine years.sas

### 1. Overall Purpose
This SAS script combines previously created fiscal year-specific B4 School Check (B4SC) analytical datasets into a single, consolidated dataset. During this process, it standardizes and combines variables derived from different Census years (2013 and 2018) using year-specific logic. It also creates new derived variables, such as grouped geographic areas, recategorized indicators, and flags for B4SC non-completion. The final output is a comprehensive dataset spanning multiple years, ready for analysis.

### 2. Input Datasets/Sources
The script reads from the following yearly datasets, which are assumed to be outputs from a previous script (e.g., `2. create b4sc dataset.sas`):

*   `dlab2.b4sc_cov_2011_junyr_full`
*   `dlab2.b4sc_cov_2012_junyr_full`
*   `dlab2.b4sc_cov_2013_junyr_full`
*   `dlab2.b4sc_cov_2014_junyr_full`
*   `dlab2.b4sc_cov_2015_junyr_full`
*   `dlab2.b4sc_cov_2016_junyr_full`
*   `dlab2.b4sc_cov_2017_junyr_full`
*   `dlab2.b4sc_cov_2018_junyr_full`

Libnames used:
*   `dlab`: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage` (though not directly used for input in this script, it's defined).
*   `dlab2`: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage/LATEST CODE/FINAL FOR OUTPUT` (location of input and output files).
*   `census`: `idi_clean_&refresh._srvprd schema=cen_clean` (defined but not directly used for input in this script).

### 3. Output Dataset(s)
The primary output dataset is:

*   **`dlab2.b4sc_allyr_FINAL`**: This dataset contains the appended and processed data from all fiscal years from 2011 to 2018.

An intermediate dataset `b4sc_raw` is created in the `work` library to hold the initially appended data before further processing.

### 4. Major Processing Steps

1.  **Append Yearly Datasets:**
    *   Concatenates the eight individual fiscal year datasets (`dlab2.b4sc_cov_2011_junyr_full` through `dlab2.b4sc_cov_2018_junyr_full`) into a single dataset called `b4sc_raw`.
    *   Drops several existing variables (`parent1_lang`, `mother_no_english`, `hh_tenure`, etc.) from `b4sc_raw` as they will be recreated with combined logic.

2.  **Combine Census-Derived Variables:** This is a core part of the script. For several variables derived from Census data, the script applies logic to choose between 2013 Census values and 2018 Census values based on the fiscal `year` of the record:
    *   **General Rule:**
        *   For fiscal years up to and including 2015 (`year le 2015`): Prioritize the 2013 Census variable. If missing, use the 2018 Census variable.
        *   For fiscal years 2016 and later (`year ge 2016`): Prioritize the 2018 Census variable. If missing, use the 2013 Census variable.
    *   **Variables Combined using this logic:**
        *   `hh_tenure` (Household Tenure): Combined from `hh_tenure_13` and `hh_tenure_18`.
        *   `parent1_highest_qual` (Mother's Highest Qualification): Combined from `parent1_highest_qual_13` and `parent1_highest_qual_18`. Missing codes ('97', '99') are blanked first.
        *   `parent1_lang` (Mother's Language): Combined from `parent1_lang_13` and `parent1_lang_18` (after converting to numeric `parent1_lang_num_13`, `parent1_lang_num_18` and handling missing codes).
        *   `hh_size` (Household Size): Combined from `hh_size_13` and `hh_size_18` (after converting to numeric `hh_size_num_13`, `hh_size_num_18` and capping values > 20 as missing).
        *   `n_mv_access` (Number of Motor Vehicles): Combined from `n_mv_access_13` and `n_mv_access_18`.
        *   `cen_ind_birth_country_code` (Child's Birth Country): Combined from `cen_ind_birth_country_code_13` and `cen_ind_birth_country_code_18`. Missing code ('9999') is blanked first.

3.  **Recode and Derive New Variables:**
    *   `gp_visit_grp`: Categorizes `gp_visits` into four groups.
    *   `sex`: Converts the original character `sex` variable to numeric `sex2` and renames it back to `sex`.
    *   `hh_benefit_inc`: Derived from 2013 Census income source variables (`inc_s7_13`, `inc_s8_13`, etc.) only.
    *   `hh_rent`: Recoded from the combined `hh_tenure`.
    *   `mother_highest_qual`: Recoded from the combined `parent1_highest_qual`.
    *   `mother_no_english`: Recoded from the combined `parent1_lang`.
    *   `hh_size_grp`: Recoded from the combined `hh_size`.
    *   `n_mv_access`: Recategorized (if >=3, then set to 2).
    *   `child_nz_born`: Set to 1 if `cen_ind_birth_country_code` is '1201' (NZ) or if `parent1_snz_uid` (proxy for birth record presence) is not missing; otherwise 0.
    *   `mother_nz_born`: Set to 1 if `parent1_birth_country_code_13` (for years <=2015) or `parent1_birth_country_code_18` (for years >=2016) is '1201' (NZ); otherwise 0.

4.  **Create Grouped TA/Ward Variable:**
    *   `grp_ta_ward_name`: Consolidates several smaller Territorial Authority (TA) or Auckland Ward names into combined categories to ensure larger group sizes for analysis (e.g., "Waitomo District" and "Otorohanga District" become "Waitomo & Otorohanga").

5.  **Create Non-Completion Indicators:**
    *   `vht_incomplete`: 1 if `vht_complete` is 0, 0 if 1, missing if `vht_complete` is missing.
    *   `nurse_incomplete`: Similar logic based on `nurse_complete`.
    *   `sdqt_incomplete`: Similar logic based on `sdqt_complete`.

6.  **Compress String Variables:**
    *   Removes single quotes from `dhb2015_name`, `ta_ward_name`, and `grp_ta_ward_name` using the `COMPRESS` function. This is often done to prevent issues in downstream processes or reporting tools that might misinterpret single quotes.

### 5. Key Variables Created/Used
This script focuses on combining and deriving variables for the final multi-year dataset.

**Key variables created or significantly modified by combining logic:**
*   `year`: Retained from individual year files, crucial for the combining logic.
*   `hh_tenure`: Combined from `hh_tenure_13` and `hh_tenure_18`.
*   `parent1_highest_qual`: Combined from `parent1_highest_qual_13` and `parent1_highest_qual_18`.
*   `parent1_lang`: Combined from `parent1_lang_13` and `parent1_lang_18`.
*   `hh_size`: Combined from `hh_size_13` and `hh_size_18`.
*   `n_mv_access`: Combined from `n_mv_access_13` and `n_mv_access_18`, then recategorized.
*   `cen_ind_birth_country_code`: Combined from `cen_ind_birth_country_code_13` and `cen_ind_birth_country_code_18`.

**Key new derived variables:**
*   `gp_visit_grp`: Categorical GP visit frequency.
*   `sex` (numeric): Original character variable converted to numeric.
*   `hh_benefit_inc`: Household income from benefits (based on 2013 Census).
*   `hh_rent`: Household rental status (derived from combined `hh_tenure`).
*   `mother_highest_qual`: Mother's highest qualification (derived from combined `parent1_highest_qual`).
*   `mother_no_english`: Flag for mother not speaking English (derived from combined `parent1_lang`).
*   `hh_size_grp`: Categorical household size (derived from combined `hh_size`).
*   `child_nz_born`: Flag indicating if the child was born in NZ.
*   `mother_nz_born`: Flag indicating if the mother was born in NZ.
*   `grp_ta_ward_name`: Grouped TA/Ward variable for reporting/analysis.
*   `vht_incomplete`: Flag for VHT check non-completion.
*   `nurse_incomplete`: Flag for Nurse check non-completion.
*   `sdqt_incomplete`: Flag for SDQT check non-completion.

**Variables dropped and then recreated (or effectively replaced by new combined versions):**
*   `parent1_lang`
*   `mother_no_english`
*   `hh_tenure`
*   `hh_benefit_inc`
*   `parent1_highest_qual`
*   `mother_highest_qual`
*   `hh_size`
*   `n_mv_access_18` (original yearly versions effectively replaced by the combined `n_mv_access`)
*   Some other specific variables like `los_days_grp`, `inpatient_visit_grp` were also dropped.

### 6. Macro Usage
This script **does not use macros** to iterate through years for appending data. Instead, it explicitly lists all the input datasets in the `SET` statement:
`SET dlab2.b4sc_cov_2011_junyr_full dlab2.b4sc_cov_2012_junyr_full ... ;`

---
*Documentation generated by AI agent.*
