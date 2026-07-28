output "instance_hostname" {
  description = "Private DNS name of the EC2 instance."
  value       = aws_instance.app_server.private_dns
}

output "ec2_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "application_url" {
  description = "URL to access the deployed application on the EC2 instance"
  value       = "http://${aws_instance.app_server.public_ip}:8000"
}
