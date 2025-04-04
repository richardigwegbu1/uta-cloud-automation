def lambda_handler(event, context):
    print("🔍 Scanning all running EC2 instances...")

    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    total = 0
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            total += 1
            instance_id = instance['InstanceId']
            tags = instance.get('Tags', [])
            name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'N/A')

            print(f"🖥️ Instance ID: {instance_id}")
            print(f"📛 Name: {name}")
            print("🏷️ Tags:")
            for tag in tags:
                print(f"  - {tag['Key']}: {tag['Value']}")
            print("-" * 30)

    print(f"➡️ Found {total} running instance(s).")

