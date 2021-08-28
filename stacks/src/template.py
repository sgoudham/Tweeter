from troposphere import Template
from troposphere.sqs import Queue

from util import Util

PROJECT_NAME: str = "Tweeter"
S3_QUEUE_NAME: str = "S3Queue"
TWEETER_QUEUE_NAME: str = "TwitterQueue"
DYNAMO_DB_QUEUE_NAME: str = "DynamoDbQueue"

template: Template = Template(PROJECT_NAME + "Workflow")
templateUtil: Util = Util(template)

s3_queue: Queue = templateUtil.create_queue(S3_QUEUE_NAME)
tweeter_queue: Queue = templateUtil.create_queue(TWEETER_QUEUE_NAME)
dynamo_db_queue: Queue = templateUtil.create_queue(DYNAMO_DB_QUEUE_NAME)

print(template.to_json())
