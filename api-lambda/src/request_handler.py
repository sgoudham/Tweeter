import json

from boto3 import Session
from decouple import config


def event_handler(event, context):
    session: Session = configure_boto3_session()
    client = session.client("sns")

    client.publish(
        TargetArn=config("sns_topic_arn"),
        Message=json.dumps({'default': json.dumps(event)}),
        MessageStructure='json'
    )

    return "Tweet Successfully Sent"


def configure_boto3_session() -> Session:
    return Session(
        aws_access_key_id=config("aws_access_key_id"),
        aws_secret_access_key=config("aws_secret_access_key"),
        region_name="eu-west-1"
    )
