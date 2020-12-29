from __future__ import division, print_function, unicode_literals

from datetime import datetime
import logging
import json
import sys
import time
import argparse
import re

import boto3
import botocore

import utils

cf = boto3.client('cloudformation') 
log = logging.getLogger('deploy.cf.create_or_update') 
stackset_id = ''

def create_stackset(name, template_data, parameter_data, model):
    # Create the StackSet
    try:
        response = cf.create_stack_set(
            StackSetName=name,
            TemplateBody=template_data,
            Parameters=parameter_data,
            Capabilities=['CAPABILITY_NAMED_IAM'],
            PermissionModel=model,
            AutoDeployment={
                'Enabled': True,
                'RetainStacksOnAccountRemoval': False
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            set_id = response['StackSetId']
        else:
            raise Exception("HTTP Error: {}".format(response))
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NameAlreadyExistsException':
            raise Exception("A StackSet called {} already exists.".format(name))
        else:
            raise Exception("Unexpected error: {}".format(e))
    return set_id

def create_stackset_instances(name, accounts, targets, regions, self_managed_permission):
    try:
        if self_managed_permission:
            response = cf.create_stack_instances(
                StackSetName=name,
                Accounts=accounts,
                Regions=regions,
                OperationPreferences = {
                    'FailureTolerancePercentage': 80,
                    'MaxConcurrentCount': 2
                }
            )
        else:    
            response = cf.create_stack_instances(
                StackSetName=name,
                DeploymentTargets=targets,
                Regions=regions,
                OperationPreferences = {
                    'FailureTolerancePercentage': 80,
                    'MaxConcurrentCount': 2
                }
            )
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'OperationInProgressException':
            raise Exception(
                "Create stack instances operation in progress for {}.".format(
                    name))
        elif e.response['Error']['Code'] == 'Throttling':
            raise Exception(
                "Throttling exception encountered while creating stack instances.")
        elif e.response['Error']['Code'] == 'StackSetNotFoundException':
            raise Exception(
                "No StackSet matching {}. You must create before creating stack instances.".format(
                    name))
        else:
            raise Exception("Error creating stack instances: {}".format(e))


if __name__ == '__main__':
    # Setup command line arguments
    parser = argparse.ArgumentParser(description='Create Stackset and Instances')
    parser.add_argument('--name', type=str, required=True, help="Stackset Name")
    parser.add_argument('--template', type=str, required=True, help='Path to Cloudformation template file')
    parser.add_argument('--parameters', type=str, help='Path to parameters json file')
    parser.add_argument('--self', action="store_true", help="indicate if permission model self managed")
    parser.add_argument('--enabled_regions', type=str, help="comma separated list of regions to deploy stackset instances. If not specified, all available regions deployed")
    parser.add_argument('--manage_account', type=str, help="AccountId for Management Account")
    parser.add_argument('--ou', type=str, required=True, help="Orgnaization ID")
    args = parser.parse_args()

    self_managed_permission = args.self
    parameter_data = []

    if utils.stackset_exists(args.name):
        print('Stackset {} existed'.format(args.name))
    else:
        print('Creating stackset {}'.format(args.name))
        template_data = utils.parse_template(args.template)
        if args.parameters != None:
            parameter_data = utils.parse_parameters(args.parameters)
        if self_managed_permission:
            model = 'SELF_MANAGED'
        else:
            model = 'SERVICE_MANAGED'
        stackset_id = create_stackset(args.name, template_data, parameter_data, model)
        print('Wating 5 seconds for stackset {} creation...'.format(args.name))
        time.sleep(5)
        if stackset_id != '':
            print('Stackset {} created successfully'.format(args.name))

    accounts = [args.manage_account]
    targets = {
        'OrganizationalUnitIds': [
            args.ou,
        ]
    }
    regions = [str(item) for item in args.enabled_regions.split(',')]
    
    response = create_stackset_instances(args.name, accounts, targets, regions, self_managed_permission)
    operation_id = response['OperationId']
    if operation_id != '':
        print('Start to create instances for stackset {}'.format(args.name))

        

