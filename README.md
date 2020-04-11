# EC2 Inventory CDK stack

This project is the source code for a 3 part series of articles which provide a guide on how to use the AWS CDK.

Article can be found here:

- Part 1 - https://letsfigureout.com/2020/02/16/a-serverless-ec2-inventory-with-the-aws-cdk-part-1/
- Part 2 - https://letsfigureout.com/2020/02/16/a-serverless-ec2-inventory-with-the-aws-cdk-part-2/
- Part 3 - https://letsfigureout.com/2020/02/16/a-serverless-ec2-inventory-with-the-aws-cdk-part-3/

As per the article this project creates a serverless EC2 inventory application, leveraging the following AWS services:

- Lambda
- CloudWatch Events
- DynamoDB
- SQS

All this is built and deployed using the AWS CDK.

## Prerequisites

- AWS CDK >= 1.32.2
- Python >= 3.8

## Deploying

Clone repository

```
$ git clone git@github.com:letsfigureout/ec2inventory.git
```

Create a virtual environment for the project

```
$ cd ec2inventory
$ python3 -m virtualenv .env
```

Install requirements

```
$ source .env/bin/activate
(.env) $ pip install -r requirements.txt
```

Deploy stack

```
(.env) $ cdk deploy
```

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
