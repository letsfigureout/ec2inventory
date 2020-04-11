import os
from datetime import datetime
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

try:
    dynamodb = boto3.resource('dynamodb')
    inventory_table = dynamodb.Table(os.getenv('inventory_table'))
except Exception as e:
    raise e

def handler(event, context):
    #boto3.resource('dynamodb')
    # Used to deserialize the DynamoDB stream
    deserializer = boto3.dynamodb.types.TypeDeserializer()

    for record in event["Records"]:
        instance = {k: deserializer.deserialize(v) for k, v in record['dynamodb']['NewImage'].items()}
        inventory(instance['instance-id'])


def inventory(instance_id: dict):
    ec2 = boto3.client('ec2')
    check_inventory = inventory_table.query(
        KeyConditionExpression=Key('instance-id').eq(instance_id))

    if check_inventory['Count'] != 0:
        print(f"Instance {instance_id} exists in inventory, deleting existing record")
        for i in check_inventory['Items']:
            inventory_table.delete_item(
                    Key={'instance-id': i['instance-id'],
                         'time': i['time'],
                    })

    inventory = ec2.describe_instances(
        InstanceIds=[instance_id])
    
    instance = inventory['Reservations'][0]['Instances'][0]
    # This is the inventory record, we will extract out some important fields and keep the whole
    # inventory data in the 'Inventory' field.
    inventory_table.put_item(
        Item={
                'instance-id': instance_id,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'State': instance['State']['Name'],
                'ImageId': instance['ImageId'],
                'InstanceType': instance['ImageId'],
                'KeyName': instance['KeyName'],
                'Tags': instance.get('Tags', 'None'),
                'VpcId': instance['VpcId'],
                'Inventory': str(instance),
            }
        )
    print(f"Record updated for {instance_id}") 