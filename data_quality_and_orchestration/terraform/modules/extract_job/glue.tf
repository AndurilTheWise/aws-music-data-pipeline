resource "aws_glue_connection" "rds_connection" {
  name = "${var.project}-connection-rds"

  connection_properties = {
    JDBC_CONNECTION_URL = "jdbc:postgresql://${var.host}:${var.port}/${var.database}"
    USERNAME            = var.username
    PASSWORD            = var.password
  }

  physical_connection_requirements {
    availability_zone      = data.aws_subnet.public_a.availability_zone
    security_group_id_list = [data.aws_security_group.db_sg.id]
    subnet_id              = data.aws_subnet.public_a.id
  }
}

resource "aws_glue_job" "rds_ingestion_etl_job" {
  name         = "${var.project}-rds-extract-job"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"
  connections  = [aws_glue_connection.rds_connection.name]

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.extract_songs_script_key}"
    python_version  = 3
  }

  default_arguments = {
    "--enable-job-insights" = "true"
    "--job-language"        = "python"
    "--rds_connection"      = aws_glue_connection.rds_connection.name
    "--data_lake_bucket"    = var.data_lake_bucket
    "--ingest_date"         = var.default_ingest_date
  }

  timeout           = 5
  number_of_workers = 2
  worker_type       = "G.1X"
}

resource "aws_glue_job" "api_users_ingestion_etl_job" {
  name         = "${var.project}-api-users-extract-job"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.api_extract_script_key}"
    python_version  = 3
  }

  default_arguments = {
    "--enable-job-insights" = "true"
    "--job-language"        = "python"
    "--api_start_date"      = var.default_api_start_date
    "--api_end_date"        = var.default_api_end_date
    "--api_url"             = "${var.api_base_url}/users"
    "--target_path"         = "s3://${var.data_lake_bucket}/landing_zone/api/users"
    "--ingest_date"         = var.default_ingest_date
  }

  timeout           = 5
  number_of_workers = 2
  worker_type       = "G.1X"
}

resource "aws_glue_job" "api_sessions_ingestion_etl_job" {
  name         = "${var.project}-api-sessions-extract-job"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.api_extract_script_key}"
    python_version  = 3
  }

  default_arguments = {
    "--enable-job-insights" = "true"
    "--job-language"        = "python"
    "--api_start_date"      = var.default_api_start_date
    "--api_end_date"        = var.default_api_end_date
    "--api_url"             = "${var.api_base_url}/sessions"
    "--target_path"         = "s3://${var.data_lake_bucket}/landing_zone/api/sessions"
    "--ingest_date"         = var.default_ingest_date
  }

  timeout           = 5
  number_of_workers = 2
  worker_type       = "G.1X"
}
