variable "environment" {
  type = string
  description = "Roombaht Environment"
}

variable "security_group_id" {
  type = string
  description = "Roombaht Host SG ID"
}

variable "subnet_id" {
  type = string
  description = "Roombaht Subnet"
}

variable "ami_id" {
  type = string
  description = "AMI"
}

variable "kms_key_id" {
  type = string
  description = "KMS Key ID"
}

variable "iam_profile" {
  type = string
  description = "Instance Profile Name"
}

variable "root_size" {
  type = number
  description = "Root FS (GB)"
  default = 20
}

variable "availability_zone" {
  type = string
  description = "Availability Zone"
  default = "a"
}

output "public_ip" {
  value = aws_eip.roombaht.public_ip
}
