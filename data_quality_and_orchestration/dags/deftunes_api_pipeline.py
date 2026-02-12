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
API_URL = os.getenv("API_URL", "api.example.com")
GLUE_ROLE_NAME = os.getenv("GLUE_ROLE_NAME", "my-glue-service-role")
GLUE_ROLE_ARN = os.getenv("GLUE_ROLE_ARN", "arn:aws:iam::123456789012:role/my-glue-service-role")
CATALOG_DATABASE = os.getenv("CATALOG_DATABASE", "deftunes_silver_db")
USERS_DQ_RULESET = os.getenv("USERS_DQ_RULESET", "users_dq_ruleset")
SESSIONS_DQ_RULESET = os.getenv("SESSIONS_DQ_RULESET", "sessions_dq_ruleset")
DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", "/docker_dbt/dbt_project")
DBT_IMAGE = os.getenv("DBT_IMAGE", "dbt_custom_image")
DBT_NETWORK_CONTAINER = os.getenv("DBT_NETWORK_CONTAINER", "dbt")
API_USERS_EXTRACT_JOB_NAME = os.getenv(
    "API_USERS_EXTRACT_JOB_NAME", f"{PROJECT_NAME}-api-users-extract-job"
)
API_SESSIONS_EXTRACT_JOB_NAME = os.getenv(
    "API_SESSIONS_EXTRACT_JOB_NAME", f"{PROJECT_NAME}-api-sessions-extract-job"
)
JSON_TRANSFORM_JOB_NAME = os.getenv(
    "JSON_TRANSFORM_JOB_NAME", f"{PROJECT_NAME}-json-transform-job"
)
API_EXTRACT_SCRIPT = os.getenv("API_EXTRACT_SCRIPT", "deftunes-api-extract-job.py")
JSON_TRANSFORM_SCRIPT = os.getenv(
    "JSON_TRANSFORM_SCRIPT", "deftunes-transform-json-job.py"
)


@dag(
    default_args=default_args,
    description="DefTunes pipeline. Run AWS Glue jobs with parameters and perform data quality checks",
    schedule_interval="0 0 1 * *",  # Runs at midnight on the first day of every month
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    dag_id="deftunes_api_pipeline_dag",
)
def deftunes_pipeline():

    start = EmptyOperator(task_id="start")

    # Use a `GlueJobOperator` to create the `api_users_extract_glue_job` task. This task is in charge of creating a Glue job that will ingest the Users endpoint 
    # and save the data in JSON format in the landing zone.
    api_users_extract_glue_job = GlueJobOperator(
        task_id="api_users_extract_glue_job",
        job_name=API_USERS_EXTRACT_JOB_NAME,
        script_location=f"s3://{SCRIPTS_BUCKET_NAME}/{API_EXTRACT_SCRIPT}",
        job_desc="Glue Job to extract data from User's API endpoint",
        # The name of the role from the Terraform output `glue_role_arn`.
        iam_role_name=GLUE_ROLE_NAME,
        # `s3_bucket` is set to the scripts bucket.
        s3_bucket=f"{SCRIPTS_BUCKET_NAME}",
        region_name=AWS_REGION,
        create_job_kwargs={
            "GlueVersion": "3.0",
            "NumberOfWorkers": 2,
            "WorkerType": "G.1X",
        },
        script_args={
            "--target_path": f"s3://{DATA_BUCKET_NAME}/landing_zone/api/users",
            "--api_url": f"http://{API_URL}/users",
            "--api_start_date": "{{ ds }}",
            "--api_end_date": "{{ macros.ds_add(next_ds, -1) }}",
            "--ingest_date": "{{ next_ds }}",
        },
    )

    # This task will create the Glue job to ingest data from the Sessions endpoint.
    api_sessions_extract_glue_job = GlueJobOperator(
        task_id="api_sessions_extract_glue_job",
        job_name=API_SESSIONS_EXTRACT_JOB_NAME,
        script_location=f"s3://{SCRIPTS_BUCKET_NAME}/{API_EXTRACT_SCRIPT}",
        job_desc="Glue Job to extract data from User's API endpoint",
        iam_role_name=GLUE_ROLE_NAME,
        s3_bucket=f"{SCRIPTS_BUCKET_NAME}",
        region_name=AWS_REGION,
        create_job_kwargs={
            "GlueVersion": "3.0",
            "NumberOfWorkers": 2,
            "WorkerType": "G.1X",
        },
        script_args={
            "--target_path": f"s3://{DATA_BUCKET_NAME}/landing_zone/api/sessions",
            "--api_url": f"http://{API_URL}/sessions",
            "--api_start_date": "{{ ds }}",
            "--api_end_date": "{{ macros.ds_add(next_ds, -1) }}",
            "--ingest_date": "{{ next_ds }}",
        },
    )

    # This task will take the data in JSON format from the users and sessions endpoints and will add some metadata and perform unnest transformations. 
    # The resulting data will be stored in Iceberg format at the transformation layer. 
    json_transform_glue_job = GlueJobOperator(
        task_id="json_transform_glue_job",
        job_name=JSON_TRANSFORM_JOB_NAME,
        script_location=f"s3://{SCRIPTS_BUCKET_NAME}/{JSON_TRANSFORM_SCRIPT}",
        job_desc="Glue Job to extract data from Sessions's API endpoint",
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
            "--users_source_path": f"s3://{DATA_BUCKET_NAME}/landing_zone/api/users/",
            "--sessions_source_path": f"s3://{DATA_BUCKET_NAME}/landing_zone/api/sessions/",
            "--target_bucket_path": f"{DATA_BUCKET_NAME}",
            "--users_table": "users",
            "--sessions_table": "sessions",
        },
    )

    # This task will evaluate the rule set for users that you created with Terraform and associated with the Terraform output `users_db_ruleset_name`. 
    # You will use the same Glue Database and the `"users"` table.
    dq_check_users_job = GlueDataQualityRuleSetEvaluationRunOperator(
        task_id="dq_check_users",
        role=GLUE_ROLE_ARN,
        rule_set_names=[USERS_DQ_RULESET],
        number_of_workers=2,
        wait_for_completion=True,
        region_name=AWS_REGION,
        datasource={
            "GlueTable": {
                "TableName": "users",
                "DatabaseName": CATALOG_DATABASE,
            }
        },
    )

    # Similar task but for the sessions.
    dq_check_sessions_job = GlueDataQualityRuleSetEvaluationRunOperator(
        task_id="dq_check_sessions",
        role=GLUE_ROLE_ARN,
        rule_set_names=[SESSIONS_DQ_RULESET],
        number_of_workers=2,
        wait_for_completion=True,
        region_name=AWS_REGION,
        datasource={
            "GlueTable": {
                "TableName": "sessions",
                "DatabaseName": CATALOG_DATABASE,
            }
        },
    )

    # You will use the `DockerOperator` in the task named `task_db` to use DBT.
    task_dbt = DockerOperator(
        task_id="docker_dbt_command",
        image=DBT_IMAGE,
        api_version="auto",
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        command='bash -c "dbt --version && dbt run --profiles-dir /usr/app/.dbt --project-dir /usr/app/dbt_modeling"',
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

    start >> [api_users_extract_glue_job, api_sessions_extract_glue_job]
    [
        api_users_extract_glue_job,
        api_sessions_extract_glue_job,
    ] >> json_transform_glue_job
    json_transform_glue_job >> [dq_check_users_job, dq_check_sessions_job]
    [dq_check_users_job, dq_check_sessions_job] >> task_dbt
    task_dbt >> end


deftunes_pipeline()
