#!/bin/bash
set -euo pipefail

DE_PROJECT="${DE_PROJECT:-deftunes}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
ENV_OUT_FILE="${ENV_OUT_FILE:-./.terraform_env.sh}"

: "${TF_VAR_source_password:?Set TF_VAR_source_password before running setup.sh}"
: "${TF_VAR_redshift_password:?Set TF_VAR_redshift_password before running setup.sh}"

VPC_ID=$(aws rds describe-db-instances --db-instance-identifier "${DE_PROJECT}-rds" --output text --query "DBInstances[].DBSubnetGroup.VpcId")
PUBLIC_SUBNET_A_ID=$(aws ec2 describe-subnets --filters "Name=tag:aws:cloudformation:logical-id,Values=PublicSubnetA" "Name=vpc-id,Values=${VPC_ID}" --output text --query "Subnets[].SubnetId")
DB_SG_ID=$(aws rds describe-db-instances --db-instance-identifier "${DE_PROJECT}-rds" --output text --query "DBInstances[].VpcSecurityGroups[].VpcSecurityGroupId")
SOURCE_HOST=$(aws rds describe-db-instances --db-instance-identifier "${DE_PROJECT}-rds" --output text --query "DBInstances[].Endpoint.Address")
DATA_LAKE_BUCKET=$(aws s3api list-buckets --query "Buckets[?starts_with(Name, '${DE_PROJECT}') && ends_with(Name, 'data-lake')].Name" --output text)
REDSHIFT_HOST=$(aws redshift describe-clusters --cluster-identifier "${DE_PROJECT}-redshift-cluster" --query "Clusters[0].Endpoint.Address" --output text)
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
SCRIPTS_BUCKET="${DE_PROJECT}-${ACCOUNT_ID}-${AWS_DEFAULT_REGION}-scripts"
CATALOG_DATABASE="${DE_PROJECT//-/_}_silver_db"

cat > "${ENV_OUT_FILE}" <<EOF
export TF_VAR_project="${DE_PROJECT}"
export TF_VAR_region="${AWS_DEFAULT_REGION}"
export TF_VAR_vpc_id="${VPC_ID}"
export TF_VAR_public_subnet_a_id="${PUBLIC_SUBNET_A_ID}"
export TF_VAR_db_sg_id="${DB_SG_ID}"
export TF_VAR_source_host="${SOURCE_HOST}"
export TF_VAR_source_port="5432"
export TF_VAR_source_database="postgres"
export TF_VAR_source_username="postgresuser"
export TF_VAR_data_lake_bucket="${DATA_LAKE_BUCKET}"
export TF_VAR_catalog_database="${CATALOG_DATABASE}"
export TF_VAR_users_table="users"
export TF_VAR_sessions_table="sessions"
export TF_VAR_songs_table="songs"
export TF_VAR_redshift_role_name="${DE_PROJECT}-load-role"
export TF_VAR_redshift_host="${REDSHIFT_HOST}"
export TF_VAR_redshift_user="defaultuser"
export TF_VAR_redshift_database="dev"
export TF_VAR_redshift_port="5439"
export TF_VAR_scripts_bucket="${SCRIPTS_BUCKET}"
EOF

source "${ENV_OUT_FILE}"
export TF_VAR_source_password
export TF_VAR_redshift_password

aws s3 cp ./terraform/assets/extract_jobs/deftunes-api-extract-job.py "s3://${TF_VAR_scripts_bucket}/deftunes-api-extract-job.py"
aws s3 cp ./terraform/assets/extract_jobs/deftunes-extract-songs-job.py "s3://${TF_VAR_scripts_bucket}/deftunes-extract-songs-job.py"
aws s3 cp ./terraform/assets/transform_jobs/deftunes-transform-json-job.py "s3://${TF_VAR_scripts_bucket}/deftunes-transform-json-job.py"
aws s3 cp ./terraform/assets/transform_jobs/deftunes-transform-songs-job.py "s3://${TF_VAR_scripts_bucket}/deftunes-transform-songs-job.py"

echo "Setup completed. Environment variables written to ${ENV_OUT_FILE}."
