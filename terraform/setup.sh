#!/bin/bash

set -ex

apt-get update -y
apt-get install -y docker.io docker-compose-v2 git

usermod -aG docker ubuntu

systemctl start docker
systemctl enable docker

if [ -n "${repo_url}" ]; then
git clone "https://${gh_pat}@github.com/${repo_url}.git"
# heredoc
cat << EOF > aeroway-ventures/backend/.env
MAIL_USERNAME=${mail_username}
MAIL_PASSWORD=${mail_password}
MAIL_PORT=${mail_port}
MAIL_SERVER=${mail_server}
MAIL_FROM_NAME=${mail_from_name}
MAIL_FROM=${mail_from}
AMADEUS_API_KEY=${amadeus_api_key}
AMADEUS_API_SECRET=${amadeus_api_secret}
AMADEUS_BASE_URL=${amadeus_base_url}
JWT_SECRET_KEY=${jwt_secret_key}
JWT_ALG=${jwt_alg}
EOF 
cd aeroway-ventures/backend
docker compose -f compose.yml up -d --build

fi
