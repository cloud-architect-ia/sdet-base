variable "lambda_zip_path" {
  description = "Ruta local del ZIP de la función Lambda"
  type        = string
}

variable "athena_db" {
  description = "Nombre de la base de datos en Athena"
  type        = string
}

variable "athena_output" {
  description = "Ruta S3 para resultados de consultas de Athena"
  type        = string
}
