// 1) Documento de asunción para Lambda
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "orders_api_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

// 2) La función Lambda

resource "aws_lambda_function" "api" {
  filename      = var.lambda_zip_path
  function_name = "orders_api"
  handler       = "handler.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      ATHENA_DB     = var.athena_db
      ATHENA_OUTPUT = var.athena_output
    }
  }
}

// 3) API Gateway REST API
resource "aws_api_gateway_rest_api" "orders_api" {
  name = "orders-api"
}

// 4) Recursos y métodos
resource "aws_api_gateway_resource" "orders" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id
  parent_id   = aws_api_gateway_rest_api.orders_api.root_resource_id
  path_part   = "orders"
}

resource "aws_api_gateway_resource" "orders_client" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id
  parent_id   = aws_api_gateway_resource.orders.id
  path_part   = "{client_id}"
}

resource "aws_api_gateway_method" "get_orders" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  resource_id   = aws_api_gateway_resource.orders_client.id
  http_method   = "GET"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.client_id" = true
  }
}

resource "aws_api_gateway_integration" "get_orders_integration" {
  rest_api_id             = aws_api_gateway_rest_api.orders_api.id
  resource_id             = aws_api_gateway_resource.orders_client.id
  http_method             = aws_api_gateway_method.get_orders.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

// 5) Permiso para que API Gateway invoque Lambda
resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.orders_api.execution_arn}/*/*"
}

// 6) Deployment y Stage
resource "aws_api_gateway_deployment" "orders_api_deploy" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.orders_api.body))
  }
  lifecycle { create_before_destroy = true }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  deployment_id = aws_api_gateway_deployment.orders_api_deploy.id
  stage_name    = "prod"
}
