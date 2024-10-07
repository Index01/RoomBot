terraform {
  backend "s3" {
    bucket = "take3-terraform-state"
    region = "us-west-2"
    key = "roombaht"
  }
}

provider "aws" {
  region = "us-west-2"
}

output "dev_ip" {
  value = module.dev.public_ip
}

variable "availability_zone" {
  type = string
  description = "Availability Zone"
  default = "a"
}

variable "alt_availability_zone" {
  type = string
  description = "Alternate Availability Zone"
  default = "c"
}
