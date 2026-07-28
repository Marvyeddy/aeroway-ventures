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

resource "aws_security_group" "app_server_sg" {
  name        = "aws-server-sg"
  description = "Allow inbound traffic on port 8000"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

resource "aws_instance" "app_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  user_data_replace_on_change = true
  user_data = templatefile("./setup.sh", {
    repo_url           = var.repo_url,
    gh_pat             = var.gh_pat,
    mail_username      = var.mail_username,
    mail_password      = var.mail_password,
    mail_port          = var.mail_port,
    mail_server        = var.mail_server,
    mail_from_name     = var.mail_from_name,
    mail_from          = var.mail_from,
    amadeus_api_key    = var.amadeus_api_key,
    amadeus_api_secret = var.amadeus_api_secret,
    amadeus_base_url   = var.amadeus_base_url,
    jwt_secret_key     = var.jwt_secret_key,
    jwt_alg            = var.jwt_alg
  })

  vpc_security_group_ids = [aws_security_group.app_server_sg.id]

  tags = {
    Name = var.instance_name
  }
}



