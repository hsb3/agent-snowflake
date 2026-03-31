---
doc_id: CC-2026-001
title: Health Insurance & Medical Economics Datasets for Snowflake
type: investigation
created: 2026-03-30
status: active
tags: [snowflake, datasets, healthcare, actuarial, CMS, cybersyn]
---

# Health Insurance & Medical Economics Datasets for Snowflake

Research into publicly available datasets relevant to medical economics and actuarial science focused on health insurance, prioritizing ease of loading into Snowflake.

## Path 1: Cybersyn Foundations (Free, One-Click via Snowflake Marketplace)

[Cybersyn Foundations](https://www.cybersyn.com/public-domain-data/) is a free collection of 60+ public domain datasets already formatted for Snowflake.

**How to install:** Snowflake web UI > Data Products > Marketplace > search "Cybersyn Foundations" > click Get. Creates a shared database instantly -- no loading, no storage cost.

### Healthcare-Relevant Content

- **CMS NPPES** -- Every healthcare provider in the US (doctors, hospitals, clinics) with NPI numbers, specialties, addresses, active/deactivated status. Multiple tables: practitioner, organization, NPI index.
- **Bureau of Labor Statistics** -- Healthcare employment, wage data, CPI medical care component
- **US Census / ACS** -- Demographics by geography (joinable to provider/plan data)

### Pros
- Zero effort, instant access
- Live-updated (Cybersyn maintains the data pipeline)
- No storage cost (shared database)

### Cons
- Limited to what Cybersyn curates
- Doesn't include the richer CMS claims/utilization files

---

## Path 2: CMS Public Use Files (Manual Load, Richer Actuarial Data)

Direct-download CSVs from CMS. All verified accessible with no auth required.

### Dataset 1: Medicare Inpatient Hospitals by Provider and Service (2023)

| Attribute | Value                                                                                                                        |
| --------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Rows      | ~146,000                                                                                                                     |
| Size      | 38 MB                                                                                                                        |
| Format    | CSV                                                                                                                          |
| URL       | `https://data.cms.gov/sites/default/files/2025-05/ca1c9013-8c7c-4560-a4a1-28cf7e43ccc8/MUP_INP_RY25_P03_V10_DY23_PrvSvc.CSV` |

**Key columns:** Rndrng_Prvdr_CCN, Rndrng_Prvdr_Org_Name, Rndrng_Prvdr_State_Abrvtn, Rndrng_Prvdr_Zip5, Rndrng_Prvdr_RUCA, DRG_Cd, DRG_Desc, Tot_Dschrgs, Avg_Submtd_Cvrd_Chrg, Avg_Tot_Pymt_Amt, Avg_Mdcr_Pymt_Amt

**Actuarial use:** Hospital charge-to-payment ratios, DRG-level cost variation, geographic price differences, urban vs rural (RUCA codes). Relevant to hospital pricing, network adequacy, reserve estimation.

**Join keys:** Rndrng_Prvdr_CCN (hospital ID), Rndrng_Prvdr_State_FIPS, Rndrng_Prvdr_Zip5, DRG_Cd

### Dataset 2: Medicare Outpatient Hospitals by Provider and Service (2023)

| Attribute | Value                                                                                                                          |
| --------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Rows      | ~116,800                                                                                                                       |
| Size      | 28 MB                                                                                                                          |
| Format    | CSV                                                                                                                            |
| URL       | `https://data.cms.gov/sites/default/files/2025-08/bceaa5e1-e58c-4109-9f05-832fc5e6bbc8/MUP_OUT_RY25_P04_V10_DY23_Prov_Svc.csv` |

**Key columns:** Rndrng_Prvdr_CCN, APC_Cd, APC_Desc, Bene_Cnt, CAPC_Srvcs, Avg_Tot_Sbmtd_Chrgs, Avg_Mdcr_Alowd_Amt, Avg_Mdcr_Pymt_Amt, Outlier_Srvcs, Avg_Mdcr_Outlier_Amt

**Actuarial use:** Outpatient utilization patterns, APC-level cost analysis, charge-to-allowed ratios, outlier payments. Combined with inpatient, gives complete picture of hospital spending.

**Join keys:** Rndrng_Prvdr_CCN (joins to inpatient), Rndrng_Prvdr_State_FIPS, Rndrng_Prvdr_Zip5

### Dataset 3: Medicare Part D Spending by Drug (2019-2023)

| Attribute | Value                                                                                                                     |
| --------- | ------------------------------------------------------------------------------------------------------------------------- |
| Rows      | ~14,300                                                                                                                   |
| Size      | 5.2 MB                                                                                                                    |
| Format    | CSV                                                                                                                       |
| URL       | `https://data.cms.gov/sites/default/files/2025-05/56d95a8b-138c-4b60-84a5-613fbab7197f/DSD_PTD_RY25_P04_V10_DY23_BGM.csv` |

**Key columns (46 total):** Brnd_Name, Gnrc_Name, Mftr_Name, then per year (2019-2023): Tot_Spndng, Tot_Dsg_Unts, Tot_Clms, Tot_Benes, Avg_Spnd_Per_Dsg_Unt_Wghtd, Avg_Spnd_Per_Clm, Avg_Spnd_Per_Bene, Outlier_Flag. Plus: Chg_Avg_Spnd_Per_Dsg_Unt_22_23, CAGR_Avg_Spnd_Per_Dsg_Unt_19_23

**Actuarial use:** Drug cost trend analysis (CAGR built in), specialty drug identification, manufacturer concentration, per-beneficiary cost. Essential for pharmacy benefit pricing and trend assumptions.

**Join keys:** Brnd_Name / Gnrc_Name (joins to Part D Prescriber Geography)

### Dataset 4: Medicare Part D Prescribers by Geography and Drug (2023)

| Attribute | Value                                                                                                                     |
| --------- | ------------------------------------------------------------------------------------------------------------------------- |
| Rows      | ~115,900                                                                                                                  |
| Size      | 14 MB                                                                                                                     |
| Format    | CSV                                                                                                                       |
| URL       | `https://data.cms.gov/sites/default/files/2025-04/9fe6b8a6-0cb9-4b7c-9760-87800da010a8/MUP_DPR_RY25_P04_V10_DY23_Geo.csv` |

**Key columns:** Prscrbr_Geo_Lvl, Prscrbr_Geo_Cd, Prscrbr_Geo_Desc, Brnd_Name, Gnrc_Name, Tot_Prscrbrs, Tot_Clms, Tot_30day_Fills, Tot_Drug_Cst, Tot_Benes, Opioid_Drug_Flag, Antbtc_Drug_Flag, Antpsyct_Drug_Flag

**Actuarial use:** State-level drug cost variation, opioid prescribing patterns, low-income subsidy cost-sharing, 65+ vs under-65 utilization. Enables geographic risk adjustment and formulary analysis.

**Join keys:** Brnd_Name / Gnrc_Name (joins to Part D Spending by Drug), Prscrbr_Geo_Cd (state FIPS)

### Dataset 5: Healthcare.gov Exchange Plan Attributes PUF (PY2026)

| Attribute | Value                                                                 |
| --------- | --------------------------------------------------------------------- |
| Rows      | ~22,000                                                               |
| Size      | 32 MB                                                                 |
| Format    | CSV                                                                   |
| URL       | `https://data.healthcare.gov/datafile/py2026/plan_attributes_PUF.csv` |

**Key columns (130+):** StateCode, IssuerId, IssuerMarketPlaceMarketingName, PlanMarketingName, PlanType, MetalLevel, IsHSAEligible, CSRVariationType, IssuerActuarialValue, AVCalculatorOutputNumber, deductible/MOOP fields by Medical/Drug/Total and In-Network/Out-of-Network tiers.

**Actuarial use:** ACA plan design database. Metal level distribution, actuarial value calibration, deductible/MOOP analysis, HSA eligibility, CSR variants. Core data for individual market pricing and benefit design studies.

**Companion file (optional):** Rate PUF PY2026 -- 281 MB, ~6M rows, age-rated premiums for every plan x rating area x age. URL: `https://data.healthcare.gov/datafile/py2026/Rate_PUF.csv`

**Join keys:** StateCode, PlanId / StandardComponentId (joins to Rate PUF), IssuerId

---

## How the Datasets Relate

```
Plan Attributes PUF ---[PlanId]---> Rate PUF
       |
   [StateCode]
       |
       v
Medicare Inpatient ---[Rndrng_Prvdr_CCN]---> Medicare Outpatient
       |                                            |
   [State_FIPS / Zip5]                      [State_FIPS / Zip5]
       |                                            |
       v                                            v
Part D Prescribers ---[Brnd_Name/Gnrc_Name]---> Part D Spending by Drug
```

CMS Medicare files share Rndrng_Prvdr_State_FIPS and Rndrng_Prvdr_Zip5 for geographic joins. Part D files connect on drug name. Exchange PUFs connect via StateCode.

## Total Size (Path 2 core files)

| Dataset                         | Size        | Rows           |
| ------------------------------- | ----------- | -------------- |
| Medicare Inpatient              | 38 MB       | 146K           |
| Medicare Outpatient             | 28 MB       | 117K           |
| Part D Spending by Drug         | 5 MB        | 14K            |
| Part D Prescribers by Geography | 14 MB       | 116K           |
| Plan Attributes PUF PY2026      | 32 MB       | 22K            |
| **Total**                       | **~117 MB** | **~415K rows** |

---

## Honorable Mention: MEPS (Medical Expenditure Panel Survey)

AHRQ MEPS is the gold standard for person-level health expenditure microdata. Not recommended as a starting point due to:
- Format friction: XLSX inside ZIP files (no native CSV)
- Complex survey design requiring weights/strata/PSUs for correct inference
- Large variable counts (1,420 columns in the consolidated file)

Worth adding later for patient-centric analysis (insurance status, demographics, conditions, expenditures by payer source).

---

## Recommendation

1. **Start with Cybersyn Foundations** -- instant, zero effort, gets healthcare provider data immediately
2. **Then load 2-3 CMS files** -- inpatient + outpatient + plan attributes give the richest actuarial picture
3. **Add MEPS later** if person-level expenditure analysis is needed

## Sources

- [Cybersyn Foundations](https://www.cybersyn.com/public-domain-data/)
- [Cybersyn on Snowflake Marketplace](https://app.snowflake.com/marketplace/providers/GZTSZAS2KCS/Cybersyn)
- [CMS NPPES via Cybersyn](https://docs.cybersyn.com/foundations/sources/nppes/)
- [CMS Public Use Files](https://data.cms.gov)
- [Healthcare.gov Exchange PUFs](https://www.cms.gov/marketplace/resources/data/public-use-files)
- [Snowflake Public Data Catalog](https://data-docs.snowflake.com/)
