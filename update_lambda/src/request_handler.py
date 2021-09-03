from boto3 import Session
from decouple import config


def event_handler(event, context):
    session: Session = configure_boto3_session()

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    s3_key = event["Records"][0]["s3"]["object"]["key"]

    s3_client = session.client('s3')
    metadata = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
    functionArn = metadata["ResponseMetadata"]["HTTPHeaders"]["x-amz-meta-function-arn"]

    lambda_client = session.client('lambda')
    response = lambda_client.update_function_code(
        FunctionName=functionArn,
        S3Bucket=bucket_name,
        S3Key=s3_key,
        Publish=True
    )

    print(f"This is the response: {response}")


def configure_boto3_session() -> Session:
    return Session(
        aws_access_key_id=config("aws_access_key_id"),
        aws_secret_access_key=config("aws_secret_access_key"),
        region_name="eu-west-1"
    )
