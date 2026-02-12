variable "project" {
  type        = string
  description = "Project name"
}

variable "region" {
  type        = string
  description = "AWS Region"
}

variable "glue_role_arn" {
  type        = string
  description = "ARN for glue jobs execution"
}

variable "scripts_bucket" {
  type        = string
  description = "S3 Bucket for glue scripts storage"
}

variable "data_lake_bucket" {
  type        = string
  description = "S3 Bucket for glue scripts storage"
}

variable "catalog_database" {
  type        = string
  description = "Curated DB name"
  sensitive   = true
}

variable "users_table" {
  type        = string
  description = "Table to store users data"
  sensitive   = true
}

variable "sessions_table" {
  type        = string
  description = "Table to store sessions data"
  sensitive   = true
}

variable "songs_table" {
  type        = string
  description = "Table to store songs data"
  sensitive   = true
}

variable "default_ingest_date" {
  type        = string
  description = "Default ingest date passed to Glue jobs (YYYY-MM-DD)"
}

variable "transform_json_script_key" {
  type        = string
  description = "S3 object key for JSON transform Glue script"
}

variable "transform_songs_script_key" {
  type        = string
  description = "S3 object key for songs transform Glue script"
}
