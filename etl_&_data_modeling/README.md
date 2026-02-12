# ETL and Data Modeling

This module contains extraction/transformation infrastructure and dbt assets for the ETL stage.

## Structure

- `terraform/`: Glue extract/transform jobs and Redshift serving resources.
- `terraform/assets/extract_jobs/`: Glue extraction scripts.
- `terraform/assets/transform_jobs/`: Glue transformation scripts.
- `dbt_modeling/`: dbt project for modeling validation and downstream transformations.
- `scripts/`: environment setup helpers.

## Typical Workflow

```bash
cd "etl_&_data_modeling/terraform"
terraform init
terraform plan
terraform apply
```

Run dbt locally:

```bash
cd "etl_&_data_modeling/dbt_modeling"
dbt debug
dbt run
dbt test
```
