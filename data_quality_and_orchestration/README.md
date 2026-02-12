# Data Quality and Orchestration

This module contains production orchestration and quality layers for the music data platform.

## Contents

- `dags/`: Airflow DAGs for API and songs pipelines.
- `terraform/`: Infrastructure for Glue jobs, data quality rulesets, and Redshift serving schemas.
- `dbt_modeling/`: dbt serving models and BI views.
- `scripts/`: setup helpers and dbt profile/package templates.

## Execution Flow

1. Extract API and songs data with Glue jobs.
2. Transform into curated Iceberg tables.
3. Run Glue Data Quality evaluations.
4. Execute dbt transformations into serving schemas.
