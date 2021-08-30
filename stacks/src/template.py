from awacs.aws import Action, Statement, Principal, Policy
from troposphere import Template, GetAtt, Ref, Join, Output, iam, awslambda
from troposphere.apigateway import RestApi, Resource, Method, Integration, IntegrationResponse, MethodResponse, \
    Deployment, Stage
from troposphere.awslambda import Function, Code
from troposphere.s3 import Bucket, VersioningConfiguration
from troposphere.sns import Topic, Subscription
from troposphere.sqs import Queue

from util import Util

PROJECT_NAME: str = "Tweeter"
REST_API_NAME: str = "TweeterAPI"
REST_API_STAGE_NAME: str = "v1"
API_LAMBDA_NAME: str = "ApiLambda"
API_LAMBDA_KEBAB_NAME: str = "api-lambda"

UPDATE_LAMBDA_NAME = "UpdateLambda"
UPDATE_LAMBDA_KEBAB_NAME = "update-lambda"
SHARED_CONFIG_BUCKET_NAME: str = "SharedConfig"

S3_QUEUE_NAME: str = "S3Queue"
TWITTER_QUEUE_NAME: str = "TwitterQueue"
DYNAMO_DB_QUEUE_NAME: str = "DynamoDbQueue"
FANOUT_TOPIC_NAME: str = "FanoutTopic"

template: Template = Template(PROJECT_NAME + "Workflow")
templateUtil: Util = Util(template)

shared_config_bucket: Bucket = template.add_resource(
    Bucket(
        SHARED_CONFIG_BUCKET_NAME,
        VersioningConfiguration=VersioningConfiguration(
            Status="Enabled",
        ),
    ))
rest_api: RestApi = template.add_resource(RestApi(REST_API_NAME, Name=REST_API_NAME))

update_lambda_execute_statements = [
    Statement(
        Action=[
            Action("logs", "*"),
            Action("cloudwatch", "*"),
            Action("cloudformation", "DescribeStacks"),
            Action("cloudformation", "DescribeStackEvents"),
            Action("cloudformation", "DescribeStackResource"),
            Action("cloudformation", "DescribeStackResources"),
            Action("cloudformation", "GetTemplate"),
            Action("cloudformation", "List*"),
        ],
        Effect="Allow",
        Resource=["*"]
    ),
    Statement(
        Action=[
            Action("s3", "Get*"),
            Action("s3", "List*")
        ],
        Effect="Allow",
        Resource=[Join("", [GetAtt(shared_config_bucket, "Arn"), "*"])]
    )
]

update_lambda_execute_role: iam.Role = template.add_resource(
    iam.Role(
        UPDATE_LAMBDA_NAME + "ExecuteRole",
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Effect="Allow",
                    Action=[Action("sts", "AssumeRole")],
                    Principal=Principal("Service", ["lambda.amazonaws.com"])
                )
            ]
        ),
        Policies=[
            iam.Policy(
                PolicyName=UPDATE_LAMBDA_NAME + "ExecutePolicy",
                PolicyDocument=Policy(Statement=update_lambda_execute_statements)
            )
        ]
    )
)

update_lambda_code: Code = Code(
    S3Bucket=Ref(shared_config_bucket),
    S3Key=Join("", [UPDATE_LAMBDA_KEBAB_NAME, "/code/", UPDATE_LAMBDA_KEBAB_NAME, "-", "1", ".zip"])
)

update_lambda: Function = template.add_resource(
    Function(
        UPDATE_LAMBDA_NAME + "Function",
        Code=update_lambda_code,
        Description=UPDATE_LAMBDA_NAME + " Function",
        Handler="request_handler.event_handler",
        Role=GetAtt(UPDATE_LAMBDA_NAME + "ExecuteRole", "Arn"),
        Runtime="python3.9",
        Timeout=300,
        MemorySize=1024
    )
)

update_lambda_invoke_permission = template.add_resource(awslambda.Permission(
    "UpdateLambdaPermissionForS3",
    Action="lambda:InvokeFunction",
    FunctionName=Ref(update_lambda),
    Principal="s3.amazonaws.com",
    SourceArn=Join("", ["arn:aws:s3:", Ref("AWS::Region"), ":", Ref("AWS::AccountId"), ":", Ref(shared_config_bucket)])
))

api_lambda_execute_statements = [
    Statement(
        Action=[
            Action("logs", "*"),
            Action("cloudwatch", "*"),
            Action("cloudformation", "DescribeStacks"),
            Action("cloudformation", "DescribeStackEvents"),
            Action("cloudformation", "DescribeStackResource"),
            Action("cloudformation", "DescribeStackResources"),
            Action("cloudformation", "GetTemplate"),
            Action("cloudformation", "List*"),
        ],
        Effect="Allow",
        Resource=["*"]
    ),
    Statement(
        Action=[
            Action("sns", "Publish")
        ],
        Effect="Allow",
        Resource=[Ref(FANOUT_TOPIC_NAME)]
    ),
]


api_lambda_execute_role: iam.Role = template.add_resource(
    iam.Role(
        API_LAMBDA_NAME + "ExecuteRole",
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Effect="Allow",
                    Action=[Action("sts", "AssumeRole")],
                    Principal=Principal("Service", ["lambda.amazonaws.com", "apigateway.amazonaws.com"])
                )
            ]
        ),
        Policies=[
            iam.Policy(
                PolicyName=API_LAMBDA_NAME + "ExecutePolicy",
                PolicyDocument=Policy(Statement=api_lambda_execute_statements)
            )
        ]
    )
)

api_lambda_code: Code = Code(
    S3Bucket=Ref(shared_config_bucket),
    S3Key=Join("", [API_LAMBDA_KEBAB_NAME, "/code/", API_LAMBDA_KEBAB_NAME, "-", "1", ".zip"])
)

api_lambda: Function = template.add_resource(
    Function(
        API_LAMBDA_NAME + "Function",
        Code=api_lambda_code,
        Description=API_LAMBDA_NAME + " Function",
        Handler="request_handler.event_handler",
        Role=GetAtt(API_LAMBDA_NAME + "ExecuteRole", "Arn"),
        Runtime="python3.9",
        Timeout=300,
        MemorySize=1024
    )
)

api_lambda_invoke_permission = template.add_resource(awslambda.Permission(
    "APILambdaPermissionForAPIGateway",
    Action="lambda:InvokeFunction",
    FunctionName=Ref(api_lambda),
    Principal="apigateway.amazonaws.com",
    SourceArn=Join("", ["arn:aws:execute-api:", Ref("AWS::Region"), ":", Ref("AWS::AccountId"), ":", Ref(rest_api), "/*/*/*"])
))

rest_api_resource: Resource = template.add_resource(
    Resource(
        API_LAMBDA_NAME + "Resource",
        RestApiId=Ref(rest_api),
        PathPart="tweet",
        ParentId=GetAtt(REST_API_NAME, "RootResourceId")
    )
)

api_lambda_method: Method = template.add_resource(
    Method(
        API_LAMBDA_NAME + "Method",
        DependsOn=API_LAMBDA_NAME + "Function",
        RestApiId=Ref(rest_api),
        AuthorizationType="NONE",
        ResourceId=Ref(rest_api_resource),
        HttpMethod="POST",
        Integration=Integration(
            Type="AWS",
            IntegrationHttpMethod="POST",
            IntegrationResponses=[IntegrationResponse(StatusCode="200")],
            Uri=Join(
                "",
                [
                    "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/",
                    GetAtt(api_lambda, "Arn"),
                    "/invocations"
                ]
            )
        ),
        MethodResponses=[MethodResponse("SuccessResponse", StatusCode="200")]
    )
)

rest_api_deployment: Deployment = template.add_resource(
    Deployment(
        REST_API_STAGE_NAME + "Deployment",
        DependsOn=API_LAMBDA_NAME + "Method",
        RestApiId=Ref(rest_api)
    )
)

rest_api_stage: Stage = template.add_resource(
    Stage(
        REST_API_STAGE_NAME + "Stage",
        StageName=REST_API_STAGE_NAME,
        RestApiId=Ref(rest_api),
        DeploymentId=Ref(rest_api_deployment)
    )
)

template.add_output(
    [
        Output(
            "RestApiEndpoint",
            Value=Join(
                "",
                [
                    "https://",
                    Ref(rest_api),
                    ".execute-api.eu-west-1.amazonaws.com/",
                    REST_API_STAGE_NAME,
                ],
            ),
            Description="Endpoint for this stage of the api",
        )
    ]
)

s3_queue: Queue = templateUtil.create_queue(S3_QUEUE_NAME)
twitter_queue: Queue = templateUtil.create_queue(TWITTER_QUEUE_NAME)
dynamo_db_queue: Queue = templateUtil.create_queue(DYNAMO_DB_QUEUE_NAME)

fanout_topic: Topic = template.add_resource(Topic(
    FANOUT_TOPIC_NAME,
    Subscription=[
        Subscription(
            Protocol="sqs",
            Endpoint=GetAtt(s3_queue, "Arn")
        ),
        Subscription(
            Protocol="sqs",
            Endpoint=GetAtt(twitter_queue, "Arn")
        ),
        Subscription(
            Protocol="sqs",
            Endpoint=GetAtt(dynamo_db_queue, "Arn")
        )
    ]
))

templateUtil.add_queue_policy_for_write_to_topic(
    s3_queue,
    "S3QueuePolicy",
    "AllowS3QueueToWriteToFanoutTopic",
    fanout_topic
)

templateUtil.add_queue_policy_for_write_to_topic(
    twitter_queue,
    "TwitterQueuePolicy",
    "AllowTwitterQueueToWriteToFanoutTopic",
    fanout_topic
)

templateUtil.add_queue_policy_for_write_to_topic(
    dynamo_db_queue,
    "DynamoDbQueuePolicy",
    "AllowDynamoDbQueueToWriteToFanoutTopic",
    fanout_topic
)

print(template.to_json())
