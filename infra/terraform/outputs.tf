# outputs.tf

output "input_bucket" {
  description = "Nombre del bucket de entrada"
  value       = aws_s3_bucket.input.id
}

output "output_bucket" {
  description = "Nombre del bucket de salida"
  value       = aws_s3_bucket.output.id
}

output "glue_role_arn" {
  description = "ARN del rol de Glue"
  value       = aws_iam_role.glue_role.arn
}

output "glue_job_name" {
  description = "Nombre del Glue Job para ejecuciones"
  value       = aws_glue_job.transform.name
}
