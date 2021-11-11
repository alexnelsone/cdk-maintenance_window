#!/usr/bin/env python3
import os
import configparser
from himl import ConfigProcessor

from aws_cdk import core as cdk
from aws_cdk import core

from cdk_ec2_patching.cdk_ec2_patching_stack import CdkEc2PatchingStack

# TODO: Figure out how to do environments better. Needs to be more dynamic.
#       cannot include account number in config file
account = os.environ['CDK_DEFAULT_ACCOUNT']
region = os.environ['CDK_DEFAULT_REGION']
env = core.Environment(account=account, region=region)

environment = os.environ['ENV']

# we use himl to have a hierarchical config using yaml
# https://github.com/adobe/himl/blob/master/README.md
config_processor = ConfigProcessor()
path = f'config/{environment}'
filters = ()
exclude_keys = ()
output_format = "yaml"

config = config_processor.process(path=path, filters=filters, exclude_keys=exclude_keys,
                         output_format=output_format, print_data=True)

config = dict(config)

namespace = config['namespace']


app = core.App()
CdkEc2PatchingStack(app, f'{namespace}-CdkEc2PatchingStack', config=config, env=env)

app.synth()
