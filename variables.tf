variable "name" {
  description = "Name of your hook function"
}

variable "environment" {
  description = "Name of your environment"
  default     = "dev"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Desired subnet with Internet and Consul access for Lambda Function"
}

variable "security_group_ids" {
  description = "Security Group IDs to allow Internet and Consul access for Lambda function"
}

## Environment Variables for Lambda
variable "commands" {
  description = "CSV string of commands to run"
  default     = <<EOF
      echo 'hello world'
  EOF
}

variable "autoscaling_group_name" {
  description = "Name of desired auto-scaling group to apply lifecycle hook to"
}
