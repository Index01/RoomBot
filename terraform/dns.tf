resource "aws_route53_zone" "roombaht" {
  name = var.domain
  tags = {
    "Name" = "roombaht lives here"
    "repo" = "Index01/RoomBot"
  }
}

resource "aws_route53_record" "dev" {
  zone_id = aws_route53_zone.roombaht.id
  name = "dev.${var.domain}"
  type = "A"
  ttl = "300"
  records = [module.dev.public_ip]
}
