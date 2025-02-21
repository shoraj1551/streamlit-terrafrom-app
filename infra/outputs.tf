output "instance_public_ip" {
  description = "Public IP of the deployed instance"
  value       = aws_instance.web.public_ip
}
