import boto3
import time
import json
import os
import time
import logging
import jsonpickle

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# The lambda_handler Python function gets called when you run your AWS Lambda function.
def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES\r' + jsonpickle.encode(dict(**os.environ)))
    logger.info('## EVENT\r' + jsonpickle.encode(event))
    logger.info('## CONTEXT\r' + jsonpickle.encode(context))

    ssmClient = boto3.client('ssm')
    s3Client = boto3.client('s3')
    snsClient = boto3.client('sns')
    autoscalingClient = boto3.client('autoscaling')
    SNS_ARN = os.environ['SNS_ARN']
    ENVIRONMENT = os.environ['ENVIRONMENT']
    COMMANDSTRING = os.environ['COMMANDS']
    COMMANDS = COMMANDSTRING.split(",")
    NAME = os.environ['NAME']

    # Desconstruct the message from the SNS object
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info(message)

    # Pull out what we need for the lifecycle hook
    InstanceId = message['EC2InstanceId']
    LifecycleActionToken = message['LifecycleActionToken']
    LifecycleHookName = message['LifecycleHookName']
    AutoScalingGroupName = message['AutoScalingGroupName']

    # Send SSM Command to instance
    ssmCommand = ssmClient.send_command(
        InstanceIds = [
            InstanceId
        ],
        DocumentName = 'AWS-RunShellScript',
        TimeoutSeconds = 240,
        Comment = 'Run Shutdown Actions',
        Parameters = {
            'commands': COMMANDS
        }
    )

    # poll SSM until EC2 Run Command completes
    status = 'Pending'
    while status == 'Pending' or status == 'InProgress':
        time.sleep(3)
        status = (ssmClient.list_commands(CommandId=ssmCommand['Command']['CommandId']))['Commands'][0]['Status']

    if status != 'Success':
        logger.error("Failed with status " + status)
        snsResponse = snsClient.publish(
            TargetArn=SNS_ARN,
            Message='%s failed with status %s.' %(ENVIRONMENT, status)
        )
        return

    response = autoscalingClient.complete_lifecycle_action(
        LifecycleHookName=LifecycleHookName,
        AutoScalingGroupName=AutoScalingGroupName,
        LifecycleActionToken=LifecycleActionToken,
        LifecycleActionResult='CONTINUE',
        InstanceId=InstanceId
    )

    logger.info("Completed.")