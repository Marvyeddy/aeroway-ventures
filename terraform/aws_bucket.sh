#!/bin/bash

set -ex

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3api create-bucket \
    --bucket aeroway-ventures-terraform-state-bucket \
    --region eu-north-1 \
    --create-bucket-configuration LocationConstraint=eu-north-1

aws s3api put-bucket-versioning \
    --bucket aeroway-ventures-terraform-state-bucket \
    --versioning-configuration Status=Enabled
# To apply a bucket policy in shell, write the policy as a JSON file and use aws s3api put-bucket-policy

cat > s3-bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::aeroway-ventures-terraform-state-bucket"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": [
        "arn:aws:s3:::aeroway-ventures-terraform-state-bucket/prod/terraform.tfstate"
      ]
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${ACCOUNT_ID}:root"
      },
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::aeroway-ventures-terraform-state-bucket/prod/terraform.tfstate.tflock"
      ]
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket aeroway-ventures-terraform-state-bucket \
    --policy file://s3-bucket-policy.json
