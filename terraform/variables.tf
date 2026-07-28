variable "instance_name" {
  description = "Value of the EC2 instance's Name tag."
  type        = string
  default     = "aeroway-ventures"
}

variable "instance_type" {
  description = "The EC2 instance's type."
  type        = string
  default     = "t3.micro"
}

variable "repo_url" {
  description = "The URL of the repository to clone."
  type        = string
  default     = "Marvyeddy/aeroway-ventures"
}

variable "gh_pat" {
  description = "GitHub personal access token."
  type        = string
  sensitive   = true
}

variable "mail_username" {
  description = "Username for mail authentication."
  type        = string
  sensitive   = true
}

variable "mail_password" {
  description = "Password for mail authentication."
  type        = string
  sensitive   = true
}

variable "mail_port" {
  description = "Port to use for mail server."
  type        = number
  sensitive   = true
}

variable "mail_server" {
  description = "Mail server address."
  type        = string
  sensitive   = true
}

variable "mail_from_name" {
  description = "The name used in the mail FROM field."
  type        = string
  sensitive   = true
}

variable "mail_from" {
  description = "The email address used in the mail FROM field."
  type        = string
  sensitive   = true
}

variable "amadeus_api_key" {
  description = "API key for Amadeus."
  type        = string
  sensitive   = true
}

variable "amadeus_api_secret" {
  description = "API secret for Amadeus."
  type        = string
  sensitive   = true
}

variable "amadeus_base_url" {
  description = "Base URL for Amadeus API."
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Secret key used for JWT."
  type        = string
  sensitive   = true
}

variable "jwt_alg" {
  description = "Algorithm used for JWT."
  type        = string
  sensitive   = true
}
