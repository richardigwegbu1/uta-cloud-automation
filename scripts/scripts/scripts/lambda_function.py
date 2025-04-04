import boto3
import datetime
import os

# Set idle time threshold (in minutes)
IDLE_THRESHOLD_MINUTES = int(os.environ.get("IDLE_THRESHOLD_MINUTES", 60))
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Initialize clients
ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def lambda_handler(event, context):
    print("🔎 Checking for idle EC2 instances...")

    # Filter for running EC2 instances tagged with UTA-Lab:true
    response = ec2.describe_instances(
        Filters=[
            {"Name": "instance-state-name", "Values": ["running"]},
            {"Name": "tag:UTA-Lab", "Values": ["true"]}
        ]
    )

    found = sum(len(res['Instances']) for res in response['Reservations'])
    print(f"➡️ Found {found} running instance(s) with tag UTA-Lab:true")

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), instance_id)

            print(f"🔍 Checking instance {name} ({instance_id})...")

            # Time range for CPU metrics
            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(minutes=IDLE_THRESHOLD_MINUTES)

            # Get CPU utilization
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
                print(f"⛔ Stopping idle instance {name} (avg CPU: {avg_cpu:.2f}%)")
                ec2.stop_instances(InstanceIds=[instance_id])
            else:
                print(f"✅ Instance {name} is active (avg CPU: {avg_cpu:.2f}%)")

