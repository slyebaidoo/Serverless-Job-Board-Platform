import logging
import boto3
import json
import os
import uuid
import datetime

# Initialize the DynamoDB resource and table
dynamodb = boto3.resource("dynamodb", region_name=os.environ["REGION"])
table = dynamodb.Table(os.environ["JOB_TABLE"])


def lambda_handler(event, context):
    try:
        # Print the incoming event for debugging purposes
        print("event ->" + str(event))

        # Parse the request body from the event as JSON
        payload = json.loads(event["body"])
        print("payload ->" + str(payload))

        # Check if the operation is 'read' to fetch job listings
        if "operation" in payload and payload["operation"] == "read":
            # Perform a scan operation on the DynamoDB table
            response = table.scan()
            items = response["Items"]

            # Sort the items based on the 'created_at' field in descending order
            items.sort(key=lambda x: x["created_at"], reverse=True)

            # Convert items to JSON format
            json_items = [json.loads(json.dumps(item, default=str)) for item in items]

            # Return the response with the JSON-formatted job listings
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                },
                "body": json.dumps(json_items, default=str),
            }

        # If the operation is not 'read', it is assumed to be 'create'
        # Put the new job listing item into the DynamoDB table
        table.put_item(
            Item={
                "job_id": str(uuid.uuid4()),
                "title": payload["title"],
                "location": payload["location"],
                "company": payload["company"],
                "salary_min": str(payload["salary_min"]),
                "salary_max": str(payload["salary_max"]),
                "description": payload["description"],
                "created_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

        # Return the response indicating successful job listing creation
        return {
            "statusCode": 201,
            "headers": {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
            "body": '{"status":"New Job added "}',
        }
    except Exception as e:
        # Log any errors that occur during execution
        logging.error(e)

        # Return an error response with the error message
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
            "body": str(e),
        }
