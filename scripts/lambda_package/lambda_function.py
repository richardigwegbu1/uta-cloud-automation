import boto3
import os
import datetime

# ✅ Set region
REGION = os.environ.get("AWS_REGION", "us-east-1")
print(f"🌍 [DEBUG] Lambda running in region: {REGION}")

# ✅ Set idle time threshold (default = 10 minutes)
IDLE_THRESHOLD_MINUTES = int(os.environ.get("IDLE_THRESHOLD_MINUTES", 10))
print(f"⏱️ [DEBUG] Idle threshold set to {IDLE_THRESHOLD_MINUTES} minutes")

# ✅ Initialize boto3 clients
ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def lambda_handler(event, context):
    print("🔍 Checking for idle EC2 instances...")

    response = ec2.describe_instances(
        Filters=[
            {"Name": "instance-state-name", "Values": ["running"]},
            {"Name": "tag:Project", "Values": ["UTA-Lab"]},
        ]
    )

    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instances.append(instance_id)
            print(f"🖥️ Instance detected: {instance_id}")

    print(f"➡️ Found {len(instances)} lab instances.")

    for instance_id in instances:
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(minutes=IDLE_THRESHOLD_MINUTES)

        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=['Average']
        )

        datapoints = metrics.get("Datapoints", [])
        avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints) if datapoints else 0

        print(f"📊 Avg CPU for {instance_id} over last {IDLE_THRESHOLD_MINUTES} minutes: {avg_cpu:.2f}%")

        if avg_cpu < 5:
            print(f"⛔ Stopping idle instance {instance_id}")
            ec2.stop_instances(InstanceIds=[instance_id])
        else:
            print(f"✅ Instance {instance_id} is active.")

