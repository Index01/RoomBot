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

variable "domain" {
  type = string
  description = "Roombaht World Wide"
  default = "rooms.take3presents.com"
}

output "dev_ip" {
  value = module.dev.public_ip
}

output "nameservers" {
  value = aws_route53_zone.roombaht.name_servers
}
