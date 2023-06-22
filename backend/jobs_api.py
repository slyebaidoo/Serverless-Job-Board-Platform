import logging
import boto3
import json
import os
import uuid
import datetime

dynamodb = boto3.resource('dynamodb', region_name=os.environ['REGION'])
table = dynamodb.Table(os.environ["JOB_TABLE"])

def lambda_handler(event, context):
    try:
        print("event ->" + str(event))
        payload = json.loads(event["body"])
        print("payload ->" + str(payload))
        
        # # print("HTTP METHOD ->" + str(event['httpMethod']) ) 
        if 'operation' in payload and payload['operation'] == 'read' :
            
            response = table.scan() 
            items = response['Items']
            items.sort(key=lambda x: x['created_at'], reverse=True)

            #  converting iterms to json
            json_items = [json.loads(json.dumps(item, default=str)) for item in items]
            
            return  {
                'statusCode': 200,
                'body': json.dumps(json_items, default=str)
            }
              
           
        print("PUTTING ITEM") 
        table.put_item(
             Item={
                'job_id' : str(uuid.uuid4()),
                'title' : payload["title"],
                'location' : payload["location"],
                'company': payload["company"],
                'salary_min' : str(payload["salary_min"]),
                'salary_max' : str(payload["salary_max"]) ,
                'description' : payload["description"],
                'created_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            })
         
        return {
            'statusCode': 201, 
           'body': '{"status":"New Job added "}'
        }
    except Exception as e:
        logging.error(e)
        return {
            'statusCode': 500,
           'body': str(e) 
        }