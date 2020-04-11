import os
import json
import boto3

try:
    dynamodb = boto3.resource('dynamodb')
    state_table = dynamodb.Table(os.getenv('state_table'))
except Exception as e:
    raise e

def handler(event, context):

    state_list = list()

    for e in event["Records"]:
        state_change = json.loads(e['body'])
        state_list.append(state_change)

    for instance in state_list:
        print(f"Adding state change for {instance['detail']['instance-id']} : {instance['detail']['state']}")
        state_table.put_item(
            Item={
                'instance-id': instance['detail']['instance-id'],
                'time': instance['time'],
                'state': instance['detail']['state']
            }
        )