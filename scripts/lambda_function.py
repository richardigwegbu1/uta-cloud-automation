import boto3
import datetime
import pytz
import os

# Set idle time threshold (in minutes)
IDLE_THRESHOLD_MINUTES = int(os.environ.get("IDLE_THRESHOLD_MINUTES", 60))
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Initialize clients
ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

# Function to check CPU usage and stop idle instances
def lambda_handler(event, context):
    print("🔎 Checking for idle EC2 instances...")

    # Get all running instances with a tag "Project: UTA-Lab"
    response = ec2.describe_instances(
        Filters=[
            {"Name": "instance-state-name", "Values": ["running"]},
            {"Name": "tag:Project", "Values": ["UTA-Lab"]}
        ]
    )

    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])

    print(f"➡️ Found {len(instances)} active lab instances.")

    for instance_id in instances:
        # Check average CPU usage in the last 60 minutes
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

        if avg_cpu < 5:
            print(f"⛔ Stopping idle instance {instance_id} (avg CPU: {avg_cpu:.2f}%)")
            ec2.stop_instances(InstanceIds=[instance_id])
        else:
            print(f"✅ Instance {instance_id} is active (avg CPU: {avg_cpu:.2f}%)")

