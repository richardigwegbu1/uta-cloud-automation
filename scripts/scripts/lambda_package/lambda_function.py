import boto3
import os
import datetime

# ✅ Region and Threshold
REGION = os.environ.get("AWS_REGION", "us-east-1")
IDLE_THRESHOLD_MINUTES = int(os.environ.get("IDLE_THRESHOLD_MINUTES", 10))
print(f"🌍 [DEBUG] Lambda running in region: {REGION}")
print(f"⏱️ [DEBUG] Idle threshold set to {IDLE_THRESHOLD_MINUTES} minutes")

# ✅ Clients
ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def lambda_handler(event, context):
    print("🔍 Checking for idle EC2 instances...")

    # ✅ Filter EC2s with tag: Project = UTA-Lab
    response = ec2.describe_instances(
        Filters=[
            {"Name": "instance-state-name", "Values": ["running"]},
            {"Name": "tag:UTA-Lab", "Values": ["true"]}
        ]
    )

    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])

    print(f"🧾 Found {len(instances)} lab instances.")

    # ✅ Check CPU usage
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=IDLE_THRESHOLD_MINUTES)

    for instance_id in instances:
        print(f"📍 Instance detected: {instance_id}")

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
            print(f"⛔ Stopping idle instance {instance_id}...")
            ec2.stop_instances(InstanceIds=[instance_id])
        else:
            print(f"✅ Instance {instance_id} is active.")
