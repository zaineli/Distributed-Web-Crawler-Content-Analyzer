import boto3

def lambda_handler(event, context):
    ecs = boto3.client('ecs')

    response = ecs.run_task(
        cluster='scraper-cluster',
        launchType='FARGATE',
        taskDefinition='scraper-task',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': ['subnet-018729cfd1766afc7'],  # Add your subnet ID
                'assignPublicIp': 'ENABLED'
            }
        }
    )

    print("ECS Task started:", response)
