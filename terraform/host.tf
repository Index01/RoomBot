module "dev" {
  source = "./host"
  environment = "dev"
  subnet_id = aws_subnet.public.id
  security_group_id = aws_security_group.roombaht.id
  ami_id = data.aws_ami.jammy.id
  iam_profile = aws_iam_instance_profile.roombaht.name
  kms_key_id = aws_kms_key.roombaht.arn
  availability_zone = var.availability_zone
}
