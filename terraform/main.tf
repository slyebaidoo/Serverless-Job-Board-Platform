provider "aws" {
  profile = "default"
  region  = "us-east-2"
}

resource "aws_dynamodb_table" "job_table" {

  name         = "JOB"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"
  range_key       = "created_at"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "title"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }
  global_secondary_index {
    name            = "JobCategoryRatingIndex"
    hash_key        = "title"
    range_key       = "created_at"
    projection_type = "ALL"
  }

}

resource "aws_api_gateway_rest_api" "job_apigw" {
  name        = "job_apigw"
  description = "Job API Gateway"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "job" {
  rest_api_id = aws_api_gateway_rest_api.job_apigw.id
  parent_id   = aws_api_gateway_rest_api.job_apigw.root_resource_id
  path_part   = "job"
}

resource "aws_api_gateway_method" "createjob" {
  rest_api_id   = aws_api_gateway_rest_api.job_apigw.id
  resource_id   = aws_api_gateway_resource.job.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_iam_role" "JobLambdaRole" {
  name               = "JobLambdaRole"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "template_file" "joblambdapolicy" {
  template = "${file("${path.module}/policy.json")}"
}

resource "aws_iam_policy" "JobLambdaPolicy" {
  name        = "JobLambdaPolicy"
  path        = "/"
  description = "IAM policy for Job lambda functions"
  policy      = data.template_file.joblambdapolicy.rendered
}

resource "aws_iam_role_policy_attachment" "JobLambdaRolePolicy" {
  role       = aws_iam_role.JobLambdaRole.name
  policy_arn = aws_iam_policy.JobLambdaPolicy.arn
}

resource "aws_lambda_function" "CreateJobHandler" {

  function_name = "CreateJobHandler"

  filename = "../backend/jobs_api.py.zip"

  handler = "jobs_api.lambda_handler"
  runtime = "python3.8"

  environment {
    variables = {
      REGION        = "us-east-2"
      JOB_TABLE = aws_dynamodb_table.job_table.name
   }
  }

  source_code_hash = filebase64sha256("../backend/jobs_api.py.zip")

  role = aws_iam_role.JobLambdaRole.arn

  timeout     = "5"
  memory_size = "128"

}

resource "aws_api_gateway_integration" "createjob-lambda" {

  rest_api_id = aws_api_gateway_rest_api.job_apigw.id
  resource_id = aws_api_gateway_method.createjob.resource_id
  http_method = aws_api_gateway_method.createjob.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"

  uri = aws_lambda_function.CreateJobHandler.invoke_arn
}

resource "aws_lambda_permission" "apigw-CreateJobHandler" {

  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.CreateJobHandler.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.job_apigw.execution_arn}/*/POST/job"
}

resource "aws_api_gateway_deployment" "jobapistageprod" {

  depends_on = [
    aws_api_gateway_integration.createjob-lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.job_apigw.id
  stage_name  = "prod"
}

output "base_url" {
  value = aws_api_gateway_deployment.jobapistageprod.invoke_url
}