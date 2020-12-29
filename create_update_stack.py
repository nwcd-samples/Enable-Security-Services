'Update or create a stack given a name and template + params'
from __future__ import division, print_function, unicode_literals

from datetime import datetime
import logging
import json
import sys
import argparse

import boto3
import botocore

import utils
  
log = logging.getLogger('deploy.cf.create_or_update') 

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")

if __name__ == '__main__':

    # Setup command line arguments
    parser = argparse.ArgumentParser(description='Create or Update Stack')
    parser.add_argument('--name', type=str, required=True, help="Stackset Name")
    parser.add_argument('--template', type=str, required=True, help='Path to Cloudformation template file')
    parser.add_argument('--parameters', type=str, help='Path to parameters json file')
    parser.add_argument('--enabled_regions', type=str, help="comma separated list of regions to deploy stack. If not specified, will only deploy to us-east-1")
    args = parser.parse_args()
    
    # Update or create stack
    template_data = utils.parse_template(args.template)
    if args.parameters != None:
        parameter_data = utils.parse_parameters(args.parameters)
        params = {
            'StackName': args.name,
            'TemplateBody': template_data,
            'Parameters': parameter_data,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
        }
    else:
        params = {
            'StackName': args.name,
            'TemplateBody': template_data,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
        }

    regions = "us-east-1"

    if args.enabled_regions != None:
        regions = args.enabled_regions

    for region in regions.split(','):
        cf = boto3.client('cloudformation', region_name=region)
        try:
            if utils.stack_exists(args.name, region):
                print('Updating {} in region {}'.format(args.name, region))
                stack_result = cf.update_stack(**params)
                waiter = cf.get_waiter('stack_update_complete')
            else:
                print('Creating {} in region {}'.format(args.name, region))
                stack_result = cf.create_stack(**params)
                waiter = cf.get_waiter('stack_create_complete')
            print("...waiting for stack to be ready...")
            waiter.wait(StackName=args.name)
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if error_message == 'No updates are to be performed.':
                print("No changes")
            else:
                raise
        else:
            print(json.dumps(
                cf.describe_stacks(StackName=stack_result['StackId']),
                indent=2,
                default=json_serial
            ))