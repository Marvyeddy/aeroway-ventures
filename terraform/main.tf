provider "aws" {
  region = "eu-north-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  user_data = templatefile("./setup.sh", {
    repo_url           = var.repo_url
    gh_pat             = var.gh_pat
    MAIL_USERNAME      = var.mail_username
    MAIL_PASSWORD      = var.mail_password
    MAIL_PORT          = var.mail_port
    MAIL_SERVER        = var.mail_server
    MAIL_FROM_NAME     = var.mail_from_name
    MAIL_FROM          = var.mail_from
    AMADEUS_API_KEY    = var.amadeus_api_key
    AMADEUS_API_SECRET = var.amadeus_api_secret
    AMADEUS_BASE_URL   = var.amadeus_base_url
    JWT_SECRET_KEY     = var.jwt_secret_key
    JWT_ALG            = var.jwt_alg
  })

  vpc_security_group_ids = [aws_security_group.app_server_sg.id]

  tags = {
    Name = var.instance_name
  }
}

resource "aws_security_group" "app_server_sg" {
  name        = "aws-server-sg"
  description = "Allow inbound traffic on port 80"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
