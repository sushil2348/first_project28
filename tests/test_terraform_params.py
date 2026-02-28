# tests/test_terraform_params.py
"""
Simple, dependency-free checks for Terraform file(s).
- Always runs in CI.
- If Terraform files exist (e.g., infra/*.tf), validates key parameters.
- If no Terraform files exist, tests are skipped (not failed).

Adjust EXPECTED_* values if your defaults differ.
"""

from pathlib import Path
import re
import pytest

# === Configure expected Terraform values here ===
EXPECTED_REGION = "ap-south-1"
EXPECTED_INSTANCE_TYPE = "t2.micro"
EXPECTED_PROVIDER = "aws"

# Where to look for TF (kept simple per your repo)
TF_DIR = Path("infra")
TF_FILES = sorted(TF_DIR.glob("*.tf"))

@pytest.fixture(scope="module")
def tf_text():
    if not TF_FILES:
        pytest.skip("No Terraform files found under infra/*.tf — skipping TF parameter checks.")
    # Concatenate all .tf files so the tests can see provider/resources across files
    return "\n\n".join(p.read_text(encoding="utf-8") for p in TF_FILES)

def test_provider_and_region(tf_text):
    # Match: provider "aws" { ... region = "ap-south-1" ... }
    provider = re.search(r'provider\s+"([^"]+)"\s*{([^}]*)}', tf_text, flags=re.S | re.M)
    assert provider, "provider block not found in Terraform files"
    provider_name = provider.group(1)
    assert provider_name == EXPECTED_PROVIDER, f'Expected provider "{EXPECTED_PROVIDER}", found "{provider_name}"'
    provider_body = provider.group(2)
    assert re.search(
        rf'\bregion\s*=\s*"{re.escape(EXPECTED_REGION)}"', provider_body
    ), f'Expected region "{EXPECTED_REGION}" in provider block'

def test_ec2_instance_type(tf_text):
    # Find an aws_instance block and check instance_type
    inst = re.search(r'resource\s+"aws_instance"\s+"[^"]+"\s*{([^}]*)}', tf_text, flags=re.S | re.M)
    assert inst, 'resource "aws_instance" block not found'
    inst_body = inst.group(1)
    assert re.search(
        rf'\binstance_type\s*=\s*"{re.escape(EXPECTED_INSTANCE_TYPE)}"', inst_body
    ), f'Expected instance_type "{EXPECTED_INSTANCE_TYPE}" in aws_instance block'

def test_security_group_exists(tf_text):
    # Ensure an SG exists (common for EC2)
    sg = re.search(r'resource\s+"aws_security_group"\s+"[^"]+"\s*{', tf_text)
    assert sg, 'resource "aws_security_group" block not found'

def test_ami_defined_somehow(tf_text):
    """
    Require that an AMI is specified either directly or via data source.
    This keeps it generic (no hardcoded AMI ID requirement).
    Passes if either:
      - aws_instance has `ami = "..."` OR
      - a data "aws_ami" exists and is referenced by aws_instance (e.g., data.aws_ami.NAME.id)
    """
    has_direct_ami = re.search(r'resource\s+"aws_instance"\s+"[^"]+"\s*{[^}]*\bami\s*=\s*"(.*?)"', tf_text, flags=re.S)
    has_data_ami  = re.search(r'data\s+"aws_ami"\s+"[^"]+"\s*{', tf_text) and re.search(r'aws_instance".*{[^}]*\bami\s*=\s*data\.aws_ami\.', tf_text, flags=re.S)
    assert has_direct_ami or has_data_ami, "EC2 AMI not found: set `ami = \"...\"` or reference a `data \"aws_ami\"` ID."