import boto3
import os
import environ

env = environ.Env()
print(env)


def get_session_token(duration_seconds=3600):
    """
    Get a session token using existing AWS credentials
    """
    try:
        # Create STS client
        sts_client = boto3.client('sts',
                                  aws_access_key_id='',
                                  aws_secret_access_key='',
                                  region_name='us-east-1')

        print(sts_client)

        # Get session token
        response = sts_client.get_session_token(
            DurationSeconds=duration_seconds
        )

        credentials = response['Credentials']

        print("Session Token Details:")
        print(f"AccessKeyId: {credentials['AccessKeyId']}")
        print(f"SecretAccessKey: {credentials['SecretAccessKey']}")
        print(f"SessionToken: {credentials['SessionToken']}")
        print(f"Expiration: {credentials['Expiration']}")

        print(credentials)

        return credentials['AccessKeyId'], credentials['SecretAccessKey'], credentials['SessionToken']

    except Exception as e:
        print(f"Error getting session token: {e}")
        return None


# Usage
# credentials = get_session_token(3600)
