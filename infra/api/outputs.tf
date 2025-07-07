output "orders_api_invoke_url" {
  description = "URL de invocación de la API de órdenes"
  value       = aws_api_gateway_stage.prod.invoke_url
}
