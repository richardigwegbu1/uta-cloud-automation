import boto3
from botocore.exceptions import ClientError

KEY_PAIR_NAME = 'uta-lab-key'

ec2 = boto3.client('ec2')

def create_key_pair():
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
            print(f"❌ Error creating key pair: {e}")

if __name__ == "__main__":
    create_key_pair()

