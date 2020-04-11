from aws_cdk import core
from aws_cdk.aws_sqs import Queue
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode, StreamViewType
from aws_cdk.aws_iam import (
    Role,
    Policy,
    Effect,
    PolicyStatement,
    ServicePrincipal,
    ManagedPolicy,
)
from aws_cdk.aws_events import Rule, EventPattern
from aws_cdk import aws_events_targets
from aws_cdk.aws_lambda import Function, Runtime, Code, StartingPosition
from aws_cdk.aws_lambda_event_sources import SqsEventSource, DynamoEventSource


class Ec2InventoryStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # SQS queue
        state_change_sqs = Queue(
            self,
            "state_change_sqs",
            visibility_timeout=core.Duration.seconds(60)
        )

        # Dynamodb Tables
        # EC2 state changes
        tb_states = Table(
            self, "ec2_states", partition_key=Attribute(name="instance-id",
                type=AttributeType.STRING),
            sort_key=Attribute(
                name="time",
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
            stream=StreamViewType.NEW_IMAGE)

        # EC2 inventory
        tb_inventory = Table(
            self, "ec2_inventory", partition_key=Attribute(name="instance-id",
                type=AttributeType.STRING),
            sort_key=Attribute(
                name="time",
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
            stream=StreamViewType.KEYS_ONLY)

        # IAM policies - AWS managed
        basic_exec = ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        sqs_access = ManagedPolicy(self, "LambdaSQSExecution",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes"
                    ],
                    resources=[state_change_sqs.queue_arn]
                )])

        # IAM Policies
        pol_ec2_states_ro = ManagedPolicy(self, "pol_EC2StatesReadOnly",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "dynamodb:DescribeStream",
                        "dynamodb:GetRecords",
                        "dynamodb:GetItem",
                        "dynamodb:GetShardIterator",
                        "dynamodb:ListStreams"
                    ],
                    resources=[tb_states.table_arn]
                )])

        pol_ec2_states_rwd = ManagedPolicy(
            self, "pol_EC2StatesWriteDelete",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "dynamodb:DeleteItem",
                        "dynamodb:DescribeTable",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem"
                    ],
                    resources=[tb_states.table_arn]
                )])

        pol_ec2_inventory_full = ManagedPolicy(
            self, "pol_EC2InventoryFullAccess",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "dynamodb:DeleteItem",
                        "dynamodb:DescribeTable",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem"
                    ],
                    resources=[tb_inventory.table_arn]
                )])
        
        pol_lambda_describe_ec2 = ManagedPolicy(
            self, "pol_LambdaDescribeEC2",
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "ec2:Describe*"
                    ],
                    resources=["*"]
                )])

        # IAM Roles
        rl_event_capture = Role(
            self,
            'rl_state_capture',
            assumed_by=ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[basic_exec, sqs_access, pol_ec2_states_rwd]
            )

        rl_event_processor = Role(
            self,
            'rl_state_processor',
            assumed_by=ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                basic_exec,
                pol_ec2_states_ro,
                pol_ec2_states_rwd,
                pol_ec2_inventory_full,
                pol_lambda_describe_ec2])

        # event capture lambda
        lambda_event_capture = Function(
            self, "lambda_event_capture",
            handler="event_capture.handler",
            runtime=Runtime.PYTHON_3_7,
            code=Code.asset('event_capture'),
            role=rl_event_capture,
            events=[SqsEventSource(state_change_sqs)],
            environment={"state_table": tb_states.table_name}
        )

        # event processor lambda
        lambda_event_processor = Function(
            self, "lambda_event_processor",
            handler="event_processor.handler",
            runtime=Runtime.PYTHON_3_7,
            code=Code.asset('event_processor'),
            role=rl_event_processor,
            events=[
                DynamoEventSource(
                    tb_states,
                    starting_position=StartingPosition.LATEST)
            ],
            environment={
                "inventory_table": tb_inventory.table_name,
                }
        )

        # Cloudwatch Event
        event_ec2_change = Rule(
            self, "ec2_state_change",
            description="trigger on ec2 start, stop and terminate instances",
            event_pattern=EventPattern(
                source=["aws.ec2"],
                detail_type=["EC2 Instance State-change Notification"],
                detail={
                    "state": [
                        "running",
                        "stopped",
                        "terminated"]
                    }
                ),
            targets=[aws_events_targets.SqsQueue(state_change_sqs)]
        )

        # Outputs
        core.CfnOutput(self, "rl_state_capture_arn", value=rl_event_capture.role_arn)
        core.CfnOutput(self, "rl_state_processor_arn", value=rl_event_processor.role_arn)
        core.CfnOutput(self, "tb_states_arn", value=tb_states.table_arn)
        core.CfnOutput(self, "tb_inventory_arn", value=tb_inventory.table_arn)
        core.CfnOutput(self, "sqs_state_change", value=state_change_sqs.queue_arn)