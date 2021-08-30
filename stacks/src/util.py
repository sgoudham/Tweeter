from troposphere import Template, Ref, GetAtt
from troposphere.sns import Topic
from troposphere.sqs import Queue, QueuePolicy


class Util:
    def __init__(self, template: Template) -> None:
        self.template = template

    def create_queue(self, queue_name: str) -> Queue:
        return self.template.add_resource(
            Queue(
                queue_name,
                MessageRetentionPeriod=345600,
                VisibilityTimeout=300,
                ReceiveMessageWaitTimeSeconds=20,
            )
        )

    def add_queue_policy_for_write_to_topic(self, queue: Queue, queue_policy_name: str, sid: str, fanout_topic: Topic) -> None:
        self.template.add_resource(QueuePolicy(
            queue_policy_name,
            Queues=[Ref(queue)],
            PolicyDocument={
                "Version": "2008-10-17",
                "Id": "PublicationPolicy",
                "Statement": [
                    {
                        "Sid": sid,
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "*"
                        },
                        "Action": ["sqs:SendMessage"],
                        "Resource": GetAtt(queue, "Arn"),
                        "Condition": {
                            "ArnEquals": {"aws:SourceArn": Ref(fanout_topic)}
                        }
                    }
                ]
            }
        ))
