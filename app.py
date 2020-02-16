#!/usr/bin/env python3

from aws_cdk import core

from ec2inventory.ec2inventory_stack import Ec2InventoryStack


app = core.App()
Ec2InventoryStack(app, "ec2inventory")

app.synth()
