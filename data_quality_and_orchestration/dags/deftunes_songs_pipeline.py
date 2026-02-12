import os
from datetime import datetime, timedelta

from airflow.decorators import dag
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.glue import (
    GlueDataQualityRuleSetEvaluationRunOperator,
    GlueJobOperator,
)
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

default_args = {
    "owner": "airflow",
    "description": "Orchestration pipeline for Deftunes song data ingestion and transformation",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PROJECT_NAME = os.getenv("PROJECT_NAME", "deftunes")
DATA_BUCKET_NAME = os.getenv("DATA_BUCKET_NAME", "my-data-lake-bucket")
SCRIPTS_BUCKET_NAME = os.getenv("SCRIPTS_BUCKET_NAME", "my-glue-scripts-bucket")
GLUE_ROLE_NAME = os.getenv("GLUE_ROLE_NAME", "my-glue-service-role")
GLUE_ROLE_ARN = os.getenv("GLUE_ROLE_ARN", "arn:aws:iam::123456789012:role/my-glue-service-role")
CATALOG_DATABASE = os.getenv("CATALOG_DATABASE", "deftunes_silver_db")
SONGS_DQ_RULESET = os.getenv("SONGS_DQ_RULESET", "songs_dq_ruleset")
RDS_CONNECTION_NAME = os.getenv("RDS_CONNECTION_NAME", "my-rds-connection")
DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", "/docker_dbt/dbt_project")
DBT_IMAGE = os.getenv("DBT_IMAGE", "dbt_custom_image")
DBT_NETWORK_CONTAINER = os.getenv("DBT_NETWORK_CONTAINER", "dbt")
RDS_EXTRACT_JOB_NAME = os.getenv(
    "RDS_EXTRACT_JOB_NAME", f"{PROJECT_NAME}-rds-extract-job"
)
RDS_EXTRACT_SCRIPT = os.getenv(
    "RDS_EXTRACT_SCRIPT", "deftunes-extract-songs-job.py"
)
SONGS_TRANSFORM_JOB_NAME = os.getenv(
    "SONGS_TRANSFORM_JOB_NAME", f"{PROJECT_NAME}-songs-transform-job"
)
SONGS_TRANSFORM_SCRIPT = os.getenv(
    "SONGS_TRANSFORM_SCRIPT", "deftunes-transform-songs-job.py"
)


@dag(
    default_args=default_args,
    schedule_interval="0 0 1 * *",  # Runs at midnight on the first day of every month
    start_date=datetime(2023, 1, 1),
    # end_date=datetime(2023, 3, 1), # Uncomment if you want a specific end date
    catchup=False,
    max_active_runs=1,
    dag_id="deftunes_songs_pipeline_dag",
)
def deftunes_songs_pipeline():

    start = EmptyOperator(task_id="start")

    # Extract data from RDS to S3 Landing Zone (CSV)
    rds_extract_glue_job = GlueJobOperator(
        task_id="rds_extract_glue_job",
        job_name=RDS_EXTRACT_JOB_NAME,
        script_location=f"s3://{SCRIPTS_BUCKET_NAME}/{RDS_EXTRACT_SCRIPT}",
        job_desc="Glue Job to extract data from RDS",
        iam_role_name=GLUE_ROLE_NAME,
        s3_bucket=f"{SCRIPTS_BUCKET_NAME}",
        region_name=AWS_REGION,
        create_job_kwargs={
            "GlueVersion": "3.0",
            "NumberOfWorkers": 2,
            "WorkerType": "G.1X",
        },
        script_args={
            "--data_lake_bucket": f"{DATA_BUCKET_NAME}",
            "--rds_connection": RDS_CONNECTION_NAME,
            "--ingest_date": "{{ next_ds }}",
        },
    )

    # Transform CSV to Iceberg/Parquet in Silver Layer
    songs_transform_glue_job = GlueJobOperator(
        task_id="songs_transform_glue_job",
        job_name=SONGS_TRANSFORM_JOB_NAME,
        script_location=f"s3://{SCRIPTS_BUCKET_NAME}/{SONGS_TRANSFORM_SCRIPT}",
        job_desc="Glue Job to extract data from RDS",
        iam_role_name=GLUE_ROLE_NAME,
        s3_bucket=f"{SCRIPTS_BUCKET_NAME}",
        region_name=AWS_REGION,
        create_job_kwargs={
            "GlueVersion": "3.0",
            "NumberOfWorkers": 2,
            "WorkerType": "G.1X",
        },
        script_args={
            "--catalog_database": CATALOG_DATABASE,
            "--ingest_date": "{{ next_ds }}",
            "--songs_table": "songs",
            "--source_bucket_path": f"{DATA_BUCKET_NAME}",
            "--target_bucket_path": f"{DATA_BUCKET_NAME}",
        },
    )

    # Validate data quality using AWS Glue Data Quality
    dq_check_songs_job = GlueDataQualityRuleSetEvaluationRunOperator(
        task_id="dq_check_songs",
        role=GLUE_ROLE_ARN,
        rule_set_names=[SONGS_DQ_RULESET],
        number_of_workers=2,
        wait_for_completion=True,
        region_name=AWS_REGION,
        datasource={
            "GlueTable": {
                "TableName": "songs",
                "DatabaseName": CATALOG_DATABASE,
            }
        },
    )

    # Run dbt models to create Gold Layer (Star Schema)
    task_dbt = DockerOperator(
        task_id="docker_dbt_command",
        image=DBT_IMAGE,
        api_version="auto",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        command='bash -c "dbt --version && dbt debug --profiles-dir /usr/app/.dbt --project-dir /usr/app/dbt_modeling  && dbt run --profiles-dir /usr/app/.dbt --project-dir /usr/app/dbt_modeling"',
        mounts=[
            Mount(
                source=f"{DBT_PROJECT_DIR}/dbt_modeling/dbt_project.yml",
                target="/usr/app/dbt_modeling/dbt_project.yml",
                type="bind",
            ),
            
            Mount(
                source=f"{DBT_PROJECT_DIR}/dbt_modeling/models",
                target="/usr/app/dbt_modeling/models",
                type="bind",
            ),
            Mount(
                source=f"{DBT_PROJECT_DIR}/.dbt",
                target="/usr/app/.dbt",
                type="bind",
            ),
        ],
        network_mode=f"container:{DBT_NETWORK_CONTAINER}",
    )

    end = EmptyOperator(task_id="end")

    (
        start
        >> rds_extract_glue_job
        >> songs_transform_glue_job
        >> dq_check_songs_job
        >> task_dbt
        >> end
    )


deftunes_songs_pipeline()
