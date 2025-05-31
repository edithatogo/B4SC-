## SAS Script Documentation: 2. create b4sc dataset.sas

### 1. Overall Purpose
This SAS script aims to create a comprehensive analytical dataset for B4 School Check (B4SC) coverage. It starts with a denominator population (presumably of 4-year-old children for a specific fiscal year, created by a preceding script) and enriches it with a wide array of data. This includes B4SC check details, demographics (ethnicity), detailed address history and associated geographical/deprivation measures, healthcare utilization (hospital visits, GP attendance), time spent overseas, detailed Census 2013 and 2018 information (for the child, their household, dwelling, and parents), birth record details, and disability flags. The script performs numerous joins, calculations, and recodes to generate a rich dataset suitable for in-depth analysis of B4SC coverage and related factors. The process is repeated for multiple fiscal years using a macro.

### 2. Input Datasets/Sources
The script reads from a variety of sources, including SAS datasets, database tables via ODBC, and an imported CSV file. The `&refresh` macro variable (e.g., `20200720`) is used to specify the IDI refresh version for many database connections.

**Libnames Defined:**
*   `central`: `idi_clean_&refresh._srvprd schema=data`
*   `moe`: `idi_clean_&refresh._srvprd schema=moe_clean`
*   `msd`: `idi_clean_&refresh._srvprd schema=msd_clean`
*   `ird`: `idi_sandpit_srvprd schema=clean_read_ir_restrict`
*   `moh`: `idi_clean_&refresh._srvprd schema=moh_clean`
*   `acc`: `idi_clean_&refresh._srvprd schema=acc_clean`
*   `dia`: `idi_clean_&refresh._srvprd schema=dia_clean`
*   `sec`: `idi_clean_&refresh._srvprd schema=security`
*   `census`: `idi_clean_&refresh._srvprd schema=cen_clean` (used for Census 2013)
*   `metadata`: `IDI_Metadata_srvprd schema=clean_read_CLASSIFICATIONS`
*   `dlab`: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage`
*   `dlab2`: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage/LATEST CODE/FINAL FOR OUTPUT` (location for the output file)
*   `conc`: `/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/Papers/B4SC denominator/Concordance files`
*   `sandmoe`: `idi_sandpit_srvprd schema=clean_read_moe`
*   `soc`: `idi_adhoc schema=clean_read_MOH_SOCRATES`

**Primary SAS Datasets:**
*   `dlab.denominator_pop_&year._junyr`: The input denominator population for the specified fiscal year (`&year`).

**Database Tables (via Libname or ODBC Pass-through):**
*   `moh.b4sc`: B4 School Check data.
*   `central.personal_detail`: For ethnicity and other personal details.
*   `central.address_notification_full`: Used to determine child's address history.
*   `metadata.depindex2013`: NZ Deprivation Index 2013 by meshblock.
*   `moh.pub_fund_hosp_discharges_event`: Hospital admission and ED visit data.
*   `central.person_overseas_spell`: Data on time spent overseas.
*   `moh.pho_enrolment`: PHO (Primary Health Organisation) enrolment data, used for GP attendance.
*   `census.census_individual_2013`: Census 2013 individual data.
*   `census.census_household_2013`: Census 2013 household data.
*   `census.census_dwelling_2013`: Census 2013 dwelling data.
*   `dia_clean.births`: Birth record information (accessed via ODBC pass-through).
*   `cen_clean.census_individual_2018`: Census 2018 individual data (accessed via ODBC pass-through, aliased as `census18_subset`).
*   `cen_clean.census_dwelling_2018`: Census 2018 dwelling data (accessed via ODBC pass-through, aliased as `census18dwl_subset`).
*   `soc.moh_disability`: MOH SOCRATES disability data.
*   `soc.moh_referral`: MOH SOCRATES referral data (used to get referral dates for disability).
*   `sec.concordance`: Used to link `snz_moh_uid` to `snz_uid` for SOCRATES data.

**Imported CSV Files:**
*   `'/nas/DataLab/MAA/MAA2016-12 Early Childhood Development Indicators/Users/Sheree/SIA B4SC coverage/Annual Areas 2018.csv'`: Contains area concordance data (MB2018, DHB2015, TA2018, WARD2018, UA2017, MB2013). Loaded into `work.area_table_2018`.

### 3. Output Dataset(s)
The primary output dataset created by the script is:

*   **`dlab2.b4sc_cov_&year._junyr_full`**: This dataset contains the enriched B4SC data for the specified fiscal year (`&year`). For example, for the year 2013, the file would be `dlab2.b4sc_cov_2013_junyr_full`.

Numerous intermediate datasets are created in the `work` library during processing (e.g., `pop_b4sc`, `b4sc_final`, `b4sc_eth`, `b4sc_address`, `addr_nzdep`, `b4sc_hosp_counts`, `b4sc_overseas`, `b4sc_pho`, `hh_uid_13`, `with_cen_parent2_18`, `b4sc_disability_nodups`, etc.).

### 4. Major Processing Steps
The script executes a sequence of data integration and manipulation steps within the `%year` macro for each specified fiscal year:

1.  **Join with B4SC Data:** Joins the input `dlab.denominator_pop_&year._junyr` with `moh.b4sc` using `snz_uid`.
2.  **Calculate B4SC Completion Statuses:**
    *   Creates flags (`general_complete`, `vision_complete`, etc.) for each component of the B4SC based on date presence.
    *   Calculates `n_checks_complete` (sum of completed components).
    *   Derives `vht_complete` (vision and hearing) and `nurse_complete` (growth, imms, dental, PEDS, SDQ-P).
3.  **Add Ethnicity:** Joins with `central.personal_detail` to add ethnicity group flags (`euro_eth`, `maori_eth`, etc.).
4.  **Determine Address and Geographic/Deprivation Variables:** This is a multi-step process:
    *   Imports `Annual Areas 2018.csv` for area concordances (MB, TA, DHB, Ward, UA).
    *   **Latest Address before 4th Birthday:** Fetches the most recent address (`mb18a`, `ant_taa`) from `central.address_notification_full` where `ant_notification_date` is before the child's `ref_date` (first day of the month of 4th birthday).
    *   **Address After 4th Birthday (if missing):** For children with no address before `ref_date`, it takes the earliest address within 12 months after `ref_date` (`mb18b`, `ant_tab`).
    *   Combines these to get a primary meshblock (`mb18`, `mb18_num`) and TA (`ant_ta`).
    *   Joins with the imported `area_table_2018` using `mb2018_code` to get `dhb2015_code`, `dhb2015_name`, `ta2018_code`, `ta2018_name`, `WARD2018_code`, `WARD2018_name`, `ua2017_code`, `ua2017_name`, and `mb2013_code`.
    *   Converts `mb2013_code` to character format (`mb13`).
    *   Joins with `metadata.depindex2013` using `mb13` to get `nzdep2013` and `depscore2013`.
5.  **Calculate Address Changes:**
    *   Counts the number of unique address UIDs (`uid_count`), distinct meshblocks (`mb_count`), and distinct TAs (`ta_count`) from `central.address_notification_full` for the period before the child's `ref_date`.
6.  **Summarize Hospital Visit History (up to `ref_date`):**
    *   Joins with `moh.pub_fund_hosp_discharges_event`.
    *   Calculates length of stay (`los_days`), flags inpatient visits (`inpatient_visits`), and ED visits (`ed_visits`).
    *   **Excludes Birth Event:** Removes the first hospital visit if it occurs in the same month and year as the child's birth.
    *   Summarizes total `los_days`, `inpatient_visits`, and `ed_visits` per child.
7.  **Calculate Time Spent Overseas (up to `ref_date`):**
    *   Joins with `central.person_overseas_spell`.
    *   Calculates `total_days_overseas` from birth date up to `ref_date`.
    *   Categorizes this into `years_overseas`.
8.  **Add GP Attendance (up to `ref_date`):**
    *   Joins with `moh.pho_enrolment`.
    *   Counts the number of distinct `moh_pho_last_consul_date` entries before `ref_date` to get `gp_visits`.
9.  **Integrate Census 2013 Data:**
    *   Joins with `census.census_individual_2013` for child's usual residence code (`cen_ind_usu_res_code_13`), birth country, and links to household (`snz_cen_hhld_uid_13`) and dwelling (`snz_cen_dwell_uid_13`). Dwelling/household UIDs are nulled if not at usual residence.
    *   Joins with `census.census_household_2013` for household size (`hh_size_13`), tenure (`hh_tenure_13`), income sources (`inc_s7_13` etc.), and total household income (`hh_total_inc_13`).
    *   Joins with `census.census_dwelling_2013` for motor vehicle access (`n_mv_access_13`).
10. **Add Birth Record Details:**
    *   Accesses `dia_clean.births` via ODBC pass-through.
    *   Joins with the main dataset on `snz_uid`.
    *   Extracts parental UIDs (`parent1_snz_uid`, `parent2_snz_uid`), parental birth years/months, child's birth weight (`dia_bir_birth_weight_nbr`), gestation (`dia_bir_birth_gestation_nbr`), and calculates number of living siblings (`sibling_count`).
    *   Creates `gestation_grp` and `bw_grp`.
11. **Integrate Parental Census 2013 Data:**
    *   Joins with `census.census_individual_2013` separately for `parent1_snz_uid` (mother) and `parent2_snz_uid` (father) to get their smoking status, marital status, work/labour force status, language, highest qualification, and birth country.
12. **Integrate Census 2018 Data:** (Used for later years and to fill missing 2013 data)
    *   Accesses `cen_clean.census_individual_2018` and `cen_clean.census_dwelling_2018` via ODBC pass-through.
    *   Joins with `census18_subset` (child data) for child's birth country (`cen_ind_birth_country_code_18`) and dwelling UID (`snz_cen_dwell_uid_18`).
    *   Joins with `census18dwl_subset` (dwelling data) for motor vehicle access (`n_mv_access_18`), tenure (`hh_tenure_18`), and number of occupants (`hh_size_18`).
13. **Integrate Parental Census 2018 Data:**
    *   Joins with `census18_subset` separately for `parent1_snz_uid` and `parent2_snz_uid` to get their 2018 smoking status, work/labour force status, language, highest qualification, and birth country.
14. **Flag for Disability:**
    *   Joins `soc.moh_disability` with `soc.moh_referral` to get `referraldate`.
    *   Links this to the main dataset via `sec.concordance` (linking `snz_moh_uid` to `snz_uid`).
    *   Creates `disability_flag` (1 if a referral exists before `ref_date`, 0 otherwise), keeping the earliest referral.
15. **Perform Extensive Variable Recoding and Derivation:** The final data step creates many new variables by recoding existing ones or deriving new indicators. Examples include:
    *   `ta_ward`, `ta_ward_name`: Combines TA and Ward for Auckland.
    *   `nzdep_quint`: NZDep2013 quintiles.
    *   `urban`: Urban/rural classification based on `ua2017_code`.
    *   `hh_rent`: Household rental status from tenure.
    *   `mother_highest_qual`, `father_highest_qual`: Recoded parental qualifications.
    *   `mother_age`, `father_age`: Calculated parental ages at child's birth.
    *   `birth_father`: Flag for presence of father's UID.
    *   `parent1_no_english`, `parent2_no_english`: Flags if parents speak languages other than English.
    *   `hh_benefit_inc`, `hh_unemp_benefit`: Household income from benefits.
    *   Various flags: `census_flag`, `parent1_flag`, `parent2_flag`, `parent1_census_flag`, `parent2_census_flag`.
    *   `low_bw`: Low birth weight flag.
    *   Grouped variables: `hh_size_grp`, `mother_age_grp`, `inpatient_visit_grp`, `ed_visit_grp`.
    *   `res_changes`: Number of residential changes (capped at 4).
    *   `sibling_count`: Capped at 2.
    *   `year`: Stores the current fiscal year being processed.

### 5. Key Variables Created/Used
This script creates and uses a vast number of variables. Some key ones include:

*   **`&year` (Macro Variable):** The fiscal year for which the data is being processed.
*   **`snz_uid`:** Unique individual identifier.
*   **`ref_date`:** Reference date (first day of the month of the child's 4th birthday).
*   **B4SC Completion:** `general_complete`, `vision_complete`, `hearing_complete`, `growth_complete`, `dental_complete`, `imms_complete`, `peds_complete`, `sdqp_complete`, `sdqt_complete`, `n_checks_complete`, `vht_complete`, `nurse_complete`.
*   **Ethnicity:** `euro_eth`, `maori_eth`, `pacific_eth`, `asian_eth`, `melaa_eth`, `other_eth`.
*   **Address/Geography:** `mb18` (Meshblock 2018), `mb18_num`, `ant_ta` (Territorial Authority), `dhb2015_code`, `dhb2015_name`, `ta_name`, `ward_name`, `ua2017_code` (Urban Area), `mb13` (Meshblock 2013), `nzdep2013`, `depscore2013`.
*   **Recoded Geographic/Deprivation:** `ta_ward`, `ta_ward_name`, `nzdep_quint`, `urban`.
*   **Address Mobility:** `uid_count` (distinct address UIDs), `mb_count` (distinct meshblocks), `ta_count` (distinct TAs), `res_changes` (recoded number of address changes).
*   **Hospitalization:** `los_days` (length of stay), `inpatient_visits`, `ed_visits`, `inpatient_visit_grp`, `ed_visit_grp`.
*   **Overseas Time:** `total_days_overseas`, `years_overseas`.
*   **GP Attendance:** `gp_visits`.
*   **Census Child:** `cen_ind_birth_country_code_13`, `cen_ind_birth_country_code_18`.
*   **Census Household (2013):** `hh_size_13`, `hh_tenure_13`, `hh_total_inc_13`, `n_mv_access_13`. Derived: `hh_rent`, `hh_benefit_inc`, `hh_unemp_benefit`, `hh_size_grp`.
*   **Census Dwelling (2018):** `n_mv_access_18`, `hh_tenure_18`, `hh_size_18`.
*   **Birth Records:** `parent1_snz_uid`, `parent2_snz_uid`, `dia_bir_birth_weight_nbr`, `dia_bir_birth_gestation_nbr`, `sibling_count`. Derived: `gestation_grp`, `bw_grp`, `low_bw`, `child_birth_rec`.
*   **Census Parents (2013 & 2018):** `parent1_smoke_13/18`, `parent1_wklfs_13/18`, `parent1_lang_13/18`, `parent1_highest_qual_13/18`. Similar for `parent2_`. Derived: `mother_highest_qual`, `father_highest_qual`, `mother_age`, `father_age`, `mother_age_grp`, `parent1_no_english`, `parent2_no_english`.
*   **Disability:** `disability_flag`.
*   **Flags:** `census_flag`, `parent1_flag`, `parent2_flag`, `parent1_census_flag`, `parent2_census_flag`.

### 6. Macro Usage
The script uses one primary macro: `%year`.

*   **Macro Name:** `year`
*   **Parameter:**
    *   `year`: This parameter takes a year value (e.g., 2011, 2012). It is used internally to set the SAS macro variable `&year`.
*   **Role:** The `%year` macro encapsulates the entire data processing logic for creating the enriched B4SC dataset for a single fiscal year. The script calls this macro multiple times at the end (e.g., `%year(2011);`, `%year(2012);`, etc.) to generate a separate output file (`dlab2.b4sc_cov_&year._junyr_full`) for each specified year. This facilitates the automated and consistent processing of data across different time periods. The `&year` macro variable within the macro definition is dynamically updated with the value passed in each call.

---
*Documentation generated by AI agent.*
