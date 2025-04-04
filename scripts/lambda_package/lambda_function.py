import boto3
import os
import datetime

REGION = os.environ.get("AWS_REGION", "us-east-1")
print(f"🌍 Lambda running in region: {REGION}")

ec2 = boto3.client("ec2", region_name=REGION)

def lambda_handler(event, context):
    print("🔍 Scanning EC2 instances...")

    response = ec2.describe_instances()  # ✅ No filters at all

    total = 0
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            total += 1
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            tags = instance.get('Tags', [])

            print(f"🖥️ ID: {instance_id} | State: {state}")
            print("🏷️ Tags:")
            for tag in tags:
                print(f"  - {tag['Key']}: {tag['Value']}")
            print("-" * 30)

    print(f"➡️ Total EC2s found: {total}")

