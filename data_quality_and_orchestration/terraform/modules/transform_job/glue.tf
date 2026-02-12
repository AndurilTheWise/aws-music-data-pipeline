resource "aws_glue_catalog_database" "transform_db" {
  name        = var.catalog_database
  description = "Glue Catalog database for transformations"
}

resource "aws_glue_job" "json_transformation_job" {
  name         = "${var.project}-json-transform-job"
  role_arn     = var.glue_role_arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.transform_json_script_key}"
    python_version  = 3
  }

  default_arguments = {
    "--enable-job-insights"     = "true"
    "--job-language"            = "python"
    "--catalog_database"        = aws_glue_catalog_database.transform_db.name
    "--ingest_date"             = var.default_ingest_date
    "--users_source_path"       = "s3://${var.data_lake_bucket}/landing_zone/api/users/"
    "--sessions_source_path"    = "s3://${var.data_lake_bucket}/landing_zone/api/sessions/"
    "--target_bucket_path"      = var.data_lake_bucket
    "--users_table"             = var.users_table
    "--sessions_table"          = var.sessions_table
    "--datalake-formats"        = "iceberg"
    "--enable-glue-datacatalog" = true
  }

  timeout           = 5
  number_of_workers = 2
  worker_type       = "G.1X"
}

resource "aws_glue_job" "songs_transformation_job" {
  name         = "${var.project}-songs-transform-job"
  role_arn     = var.glue_role_arn
  glue_version = "4.0"

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/${var.transform_songs_script_key}"
    python_version  = 3
  }

  default_arguments = {
    "--enable-job-insights"     = "true"
    "--job-language"            = "python"
    "--catalog_database"        = aws_glue_catalog_database.transform_db.name
    "--ingest_date"             = var.default_ingest_date
    "--source_bucket_path"      = var.data_lake_bucket
    "--target_bucket_path"      = var.data_lake_bucket
    "--songs_table"             = var.songs_table
    "--datalake-formats"        = "iceberg"
    "--enable-glue-datacatalog" = true
  }

  timeout           = 5
  number_of_workers = 2
  worker_type       = "G.1X"
}
