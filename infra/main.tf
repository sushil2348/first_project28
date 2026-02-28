terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Hardcode region here
provider "aws" {
  region = "ap-south-1"
}

# Find a recent Amazon Linux 2023 AMI owned by Amazon
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["137112412989"] # Amazon Linux AMIs owner

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VERY open SSH for demo — replace with your IP/CIDR for real use
resource "aws_security_group" "demo_sg" {
  name        = "demo-ec2-sg"
  description = "Allow SSH for demo"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # ⚠️ Replace in real environments
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name  = "demo-ec2-sg"
    Owner = "Sushil"
    Env   = "sandbox"
  }
}

# Default VPC/subnet discovery (keeps config minimal)
data "aws_vpc" "default" {
  default = true
}

# Launch EC2 in default subnet (implicit if subnet not provided)
resource "aws_instance" "demo" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.demo_sg.id]

  # No key_name set -> you won't be able to SSH unless you add one
  # key_name = "existing-keypair-name"

  tags = {
    Name  = "demo-ec2"
    Owner = "Sushil"
    Env   = "sandbox"
  }
}

