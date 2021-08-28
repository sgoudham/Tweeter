from troposphere import Template

from util import Util

PROJECT_NAME = "Tweeter"
S3_QUEUE_NAME = PROJECT_NAME + "S3Queue"
TWEETER_QUEUE_NAME = PROJECT_NAME + "Queue"
DYNAMO_DB_QUEUE_NAME = PROJECT_NAME + "DynamoDbQueue"
SHARED_CONFIG_BUCKET_NAME = PROJECT_NAME + "SharedConfig"

template = Template(PROJECT_NAME + "Workflow")
templateUtil = Util(template)

s3_queue = templateUtil.create_queue(S3_QUEUE_NAME)
tweeter_queue = templateUtil.create_queue(TWEETER_QUEUE_NAME)
dynamo_db_queue = templateUtil.create_queue(DYNAMO_DB_QUEUE_NAME)

print(template.to_json())
