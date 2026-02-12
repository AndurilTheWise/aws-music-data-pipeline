# dbt Modeling (ETL Stage)

This dbt project contains lightweight models used during the ETL and data-modeling stage.

## Local Usage

```bash
cd "etl_&_data_modeling/dbt_modeling"
dbt debug
dbt run
dbt test
```

## Configuration

- `dbt_project.yml` defines model paths and materialization defaults.
- Use your own `profiles.yml` (see root `profiles.yml.example`) to point dbt to your warehouse.

## Notes

The `models/example` directory is intentionally minimal and serves as a validation scaffold for CI and environment setup.
