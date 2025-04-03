import boto3
import time
from botocore.exceptions import ClientError

# Boto3 EC2 client and resource
ec2 = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')

# Constants
KEY_PAIR_NAME = 'uta-lab-key'
SECURITY_GROUP_NAME = 'uta-lab-sg'
AMI_ID = 'ami-0c55b159cbfafe1f0'  # ✅ Red Hat Enterprise Linux (RHEL) AMI ID (update if needed)
INSTANCE_TYPE = 't3.micro'
TAG_NAME = 'UTA-Lab-Server'
REGION = 'us-east-1'

# Step 1: Create key pair
try:
    response = ec2.create_key_pair(KeyName=KEY_PAIR_NAME)
    private_key = response['KeyMaterial']
    with open(f"{KEY_PAIR_NAME}.pem", "w") as file:
        file.write(private_key)
    print(f"✅ Key pair '{KEY_PAIR_NAME}' created and saved as {KEY_PAIR_NAME}.pem")
except ClientError as e:
    if 'InvalidKeyPair.Duplicate' in str(e):
        print(f"ℹ️ Key pair '{KEY_PAIR_NAME}' already exists.")
    else:
        raise

# Step 2: Create security group
try:
    sg_response = ec2.create_security_group(
        GroupName=SECURITY_GROUP_NAME,
        Description='Security group for UTA Lab SSH access'
    )
    sg_id = sg_response['GroupId']
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print(f"✅ Security group '{SECURITY_GROUP_NAME}' created and SSH access allowed.")
except ClientError as e:
    if 'InvalidGroup.Duplicate' in str(e):
        print(f"ℹ️ Security group '{SECURITY_GROUP_NAME}' already exists.")
        sg_id = ec2.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])['SecurityGroups'][0]['GroupId']
    else:
        raise

# Step 3: Try launching Spot Instance
def request_spot_instance():
    print("⏳ Requesting Spot Instance...")
    try:
        spot = ec2.request_spot_instances(
            InstanceCount=1,
            Type='one-time',
            LaunchSpecification={
                'ImageId': AMI_ID,
                'InstanceType': INSTANCE_TYPE,
                'KeyName': KEY_PAIR_NAME,
                'SecurityGroupIds': [sg_id],
            }
        )
        request_id = spot['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        print(f"✅ Spot request made: {request_id}")
        return request_id
    except ClientError as e:
        print(f"❌ Spot request failed: {e}")
        return None

def get_spot_instance_id(request_id):
    print("🔍 Waiting for Spot instance fulfillment...")
    for _ in range(15):
        time.sleep(10)
        response = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=[request_id])
        instance_id = response['SpotInstanceRequests'][0].get('InstanceId')
        if instance_id:
            print(f"✅ Spot instance launched: {instance_id}")
            return instance_id
    print("❌ Timeout waiting for Spot instance.")
    return None

# Step 4: Fallback to On-Demand if Spot fails
def launch_on_demand():
    print("🚨 Launching On-Demand instance as fallback...")
    instance = ec2_resource.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_PAIR_NAME,
        SecurityGroupIds=[sg_id],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': TAG_NAME}]
            }
        ]
    )[0]
    print(f"✅ On-Demand instance launched: {instance.id}")
    return instance.id

# Main Execution
spot_request_id = request_spot_instance()
instance_id = None

if spot_request_id:
    instance_id = get_spot_instance_id(spot_request_id)

if not instance_id:
    instance_id = launch_on_demand()

print(f"🎯 Final instance ID: {instance_id}")

