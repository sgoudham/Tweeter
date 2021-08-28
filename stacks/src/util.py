from troposphere.sqs import Queue


class Util:
    def __init__(self, template):
        self.template = template

    def create_queue(self, queue_name):
        return self.template.add_resource(
            Queue(
                queue_name,
                MessageRetentionPeriod=345600,
                VisibilityTimeout=300,
                ReceiveMessageWaitTimeSeconds=20,
            )
        )
