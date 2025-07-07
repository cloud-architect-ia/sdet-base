provider "aws" {
  region = "us-east-1"
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "input" {
  bucket = "test-input-${random_id.suffix.hex}"
}

resource "aws_s3_bucket" "output" {
  bucket = "test-output-${random_id.suffix.hex}"
}

data "aws_iam_policy_document" "glue_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_role" {
  name               = "GlueExecutionRole"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_glue_job" "transform" {
  name     = "csv-transform-job"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.input.id}/scripts/transform.py"
  }
}

resource "aws_iam_role" "lambda_athena_role" {
  name = "lambda-athena-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
}

resource "aws_iam_role_policy_attachment" "lambda_athena_attach" {
  role       = aws_iam_role.lambda_athena_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

resource "aws_lambda_function" "api" {
  filename         = "${path.module}/../../lambda/lambda.zip"
  function_name    = "orders_api"
  handler          = "handler.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_athena_role.arn

  environment {
    variables = {
      ATHENA_DB     = "sdet_demo"
      ATHENA_OUTPUT = "s3://${aws_s3_bucket.output.id}/athena-results/"
    }
  }
}

resource "aws_api_gateway_rest_api" "orders_api" {
  name = "orders-api"
}


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

resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.orders_api.execution_arn}/*/*"
}


resource "aws_api_gateway_deployment" "orders_api_deploy" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.orders_api.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  deployment_id = aws_api_gateway_deployment.orders_api_deploy.id
  stage_name    = "prod"
  description   = "Stage de producción"
}

