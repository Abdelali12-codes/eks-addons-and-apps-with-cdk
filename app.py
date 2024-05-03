#!/usr/bin/env python3
import os

import aws_cdk as cdk

from eks_python.eks_python_stack import EksPythonStack
from eks_python.configuration.config import (REGION, ACCOUNT)

app = cdk.App()
env = cdk.Environment(account=ACCOUNT, region=REGION)

EksPythonStack(app, "EksPythonStack",
    env=env,
    )
app.synth()
