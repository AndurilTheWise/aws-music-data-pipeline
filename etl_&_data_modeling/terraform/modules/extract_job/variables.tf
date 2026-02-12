variable "project" {
  type        = string
  description = "Project name"
}

variable "region" {
  type        = string
  description = "AWS Region"
}

variable "public_subnet_a_id" {
  type        = string
  description = "Private subnet A ID"
}

variable "db_sg_id" {
  type        = string
  description = "Security group ID for RDS"
}

variable "host" {
  type        = string
  description = "RDS host"
}

variable "port" {
  type        = number
  description = "RDS port"
  default     = 3306
}

variable "database" {
  type        = string
  description = "RDS database name"
}

variable "username" {
  type        = string
  description = "RDS username"
}

variable "password" {
  type        = string
  description = "RDS password"
  sensitive   = true
}

variable "data_lake_bucket" {
  type        = string
  description = "Data lake bucket name"
}

variable "scripts_bucket" {
  type        = string
  description = "Data lake bucket name"
}

variable "api_base_url" {
  type        = string
  description = "Base URL for source API, without trailing slash"
}

variable "default_api_start_date" {
  type        = string
  description = "Default API extraction start date (YYYY-MM-DD)"
}

variable "default_api_end_date" {
  type        = string
  description = "Default API extraction end date (YYYY-MM-DD)"
}

variable "api_extract_script_key" {
  type        = string
  description = "S3 object key for API extract Glue script"
}

variable "extract_songs_script_key" {
  type        = string
  description = "S3 object key for songs extract Glue script"
}
