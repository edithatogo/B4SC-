## SAS Script Documentation: 1. create denominator pop.sas

### 1. Overall Purpose
This SAS script is designed to create a denominator population of 4-year-old children for a specific fiscal year. It filters the Stats NZ resident population, incorporates personal details (birth date, sex), accounts for deaths, calculates age as of June 30th of the specified year, and excludes children who have spent more than 6 months overseas in the preceding year. The final output is a dataset containing individuals who meet these criteria, intended for further analysis, likely related to B4 School Check (B4SC) coverage or similar child development indicators.

### 2. Input Datasets/Sources
The script reads from the following unique database tables and libnames, using an IDI refresh specified by the `&refresh` macro variable:

*   **central.snz_res_pop:** Used to get the base resident population for the specified year.
*   **central.personal_detail:** Joined to add personal characteristics like birth date and sex.
*   **dia_clean.deaths:** Used to extract death information for individuals.
*   **central.person_overseas_spell:** Used to calculate the amount of time individuals spent overseas.
*   **moh.pop_cohort_demographics:** Joined to get the NZ resident status code.

The script also defines several libnames pointing to different schemas within the IDI Clean environment:
*   `central`: `idi_clean_&refresh._srvprd schema=data`
*   `moe`: `idi_clean_&refresh._srvprd schema=moe_clean`
*   `msd`: `idi_clean_&refresh._srvprd schema=msd_clean`
*   `moh`: `idi_clean_&refresh._srvprd schema=moh_clean`
*   `acc`: `idi_clean_&refresh._srvprd schema=acc_clean`
*   `dia`: `idi_clean_&refresh._srvprd schema=dia_clean`
*   `sec`: `idi_clean_&refresh._srvprd schema=security`
*   `dlab`: Points to a user-specific NAS location: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage`

### 3. Output Dataset(s)
The primary output dataset is:

*   **dlab.denominator_pop_&year._junyr:** This dataset contains the final denominator population for the specified fiscal year (`&year`). The `&year` macro variable is resolved at runtime (e.g., `dlab.denominator_pop_2011_junyr`).

Intermediate datasets created during processing include: `totalpop`, `finalpop2`, `dia_deaths`, `finalpop3`, `finalpop_age`, `overseas_spells_1yr`, `overseas_time_1yr`, `finalpop_res`, and `denominator_pop`. These are generally temporary work tables.

### 4. Major Processing Steps
The script follows these major processing steps, executed within the `%fyear` macro for each specified year:

1.  **Set Fiscal Year Parameters:** Macro variables `&year`, `&startyrsql`, `&endyrsql`, and `&refresh` are set. `&prevyear` is calculated.
2.  **Define Libraries:** Libnames for various IDI Clean schemas and a user DLab space are defined.
3.  **Extract Base Resident Population:** Filters `central.snz_res_pop` for records where `srp_ref_date` is "30JUN&year."d, keeping only `snz_uid`. (Output: `totalpop`)
4.  **Add Personal Details:** Joins `totalpop` with `central.personal_detail` on `snz_uid` to add `snz_birth_year_nbr`, `snz_birth_month_nbr`, `snz_sex_gender_code`, and `snz_spine_ind`. (Output: `finalpop2`)
5.  **Extract Death Information:** Selects distinct `snz_uid`, `dia_dth_death_year_nbr`, and `dia_dth_death_month_nbr` from `dia_clean.deaths` for deaths occurring between 1990 and the specified `&year`. (Output: `dia_deaths`)
6.  **Merge Death Information:** Joins `finalpop2` with `dia_deaths` on `snz_uid`. (Output: `finalpop3`)
7.  **Calculate Age and Filter:**
    *   Calculates `age` as of June 30th of `&year` based on `snz_birth_year_nbr` and `snz_birth_month_nbr`.
    *   Filters to keep only individuals where `age` is 4.
    *   Removes individuals who died before the start of the fiscal year (`dia_dth_death_year_nbr < &year`).
    *   Flags individuals who died during the fiscal year (`died_&year.`).
    *   Creates `ref_date` (first day of the month of the 4th birthday).
    *   Renames `snz_sex_gender_code` to `sex`.
    *   Keeps selected variables. (Output: `finalpop_age`)
8.  **Calculate Time Spent Overseas:**
    *   Extracts overseas spells from `central.person_overseas_spell` that overlap with the 12 months prior to "30JUN&year.". (Output: `overseas_spells_1yr`)
    *   Calculates the duration of each spell within this 12-month window (`time_to_add`). (Output: `overseas_time_1yr`)
    *   Sums the `time_to_add` for each `snz_uid` to get `days_overseas_last1`. (Output: `time_overseas_1yr`)
9.  **Filter Based on Time Overseas:**
    *   Merges `finalpop_age` with `time_overseas_1yr`.
    *   Removes individuals if `days_overseas_last1` is greater than 183 days. (Output: `finalpop_res`)
10. **Join with Resident Status Codes:** Joins `finalpop_res` with `moh.pop_cohort_demographics` on `snz_uid` to add `moh_pop_nz_res_status_code`. (Output: `denominator_pop`)
11. **Create Final Output Dataset:** Saves the `denominator_pop` table to `dlab.denominator_pop_&year._junyr`.

### 5. Key Variables Created/Used
*   **`&year` (Macro Variable):** Specifies the end of the financial year of interest (e.g., 2011). Used extensively in date filters and output dataset naming.
*   **`&refresh` (Macro Variable):** Specifies the IDI refresh version to use for data extraction (e.g., 20200720).
*   **`snz_uid`:** Unique Stats NZ individual identifier, used as the primary key for joining datasets.
*   **`srp_ref_date`:** Reference date in `snz_res_pop`, used to filter for the population at "30JUN&year.".
*   **`snz_birth_year_nbr`, `snz_birth_month_nbr`:** Used to calculate age.
*   **`snz_sex_gender_code` (renamed to `sex`):** Individual's sex/gender.
*   **`dia_dth_death_year_nbr`, `dia_dth_death_month_nbr`:** Year and month of death. Used to filter out individuals who died before the period of interest and to flag those who died within it.
*   **`age`:** Calculated age of the individual as of June 30th of `&year`. Used to filter for 4-year-olds.
*   **`died_&year.`:** Flag (1/0) indicating if the person died during the fiscal year `&year`.
*   **`ref_date`:** Calculated reference date, set to the first day of the month of the child's 4th birthday.
*   **`pos_applied_date`, `pos_ceased_date`, `pos_day_span_nbr`:** Variables from `person_overseas_spell` used to determine time spent overseas.
*   **`days_overseas_last1`:** Calculated total number of days spent overseas in the 12 months preceding "30JUN&year.". Used to filter out individuals residing overseas for more than 183 days.
*   **`moh_pop_nz_res_status_code`:** NZ resident status code from MOH data.

### 6. Macro Usage
The script uses one primary macro: `%fyear`.

*   **Macro Name:** `fyear`
*   **Parameters:**
    *   `yr`: Corresponds to the `&year` macro variable, representing the end year of the fiscal period (e.g., 2011).
    *   `st`: Corresponds to the `&startyrsql` macro variable, representing the start date of a 5-year window for data extraction (e.g., '2006-07-01'). *Note: The comment indicates this should align with 5 years *before* the fiscal year of interest, but its direct usage in the provided script snippet for filtering main population tables is not apparent beyond being set as a macro variable. It might be intended for other processes or was part of an older logic.*
    *   `en`: Corresponds to the `&endyrsql` macro variable, representing the end date of this 5-year window, aligning with the end of the fiscal year of interest (e.g., '2011-06-30'). *Similar to `&startyrsql`, its direct filtering use in the main flow is not explicit for core population selection beyond being set.*
*   **Role:** The `%fyear` macro encapsulates the entire data processing logic for a single fiscal year. By calling this macro multiple times with different year parameters (as shown at the end of the script: `%fyear (2011, '2006-07-01', '2011-06-30');`, `%fyear (2012, ...);`, etc.), the script automates the creation of the denominator population dataset for each of those fiscal years. This allows for repeatable and consistent processing across different time periods. The macro variables `&year`, `&startyrsql`, and `&endyrsql` are dynamically updated for each call to `%fyear`.

---
*Documentation generated by AI agent.*
