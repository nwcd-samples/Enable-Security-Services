import boto3
import botocore
import json

CIS_STANDARD_RESOURCE = 'ruleset/cis-aws-foundations-benchmark/v/1.2.0'

CIS_STANDARD_ARN = 'arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0'
"arn:aws:securityhub:us-west-2::standards/pci-dss/v/3.2.1"

def get_standard_arn_for_region_and_resource(region, standard_resource):
    if standard_resource == CIS_STANDARD_ARN or standard_resource == CIS_STANDARD_RESOURCE:
        return CIS_STANDARD_ARN
    else:
        return 'arn:{partition}:securityhub:{region}::{resource}'.format(partition='aws', region=region, resource=standard_resource)

def parse_template(template):
    cf = boto3.client('cloudformation')
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cf.validate_template(TemplateBody=template_data)
    return template_data


def parse_parameters(parameters):
    with open(parameters) as parameter_fileobj:
        parameter_data = json.load(parameter_fileobj)
    return parameter_data


def stack_exists(stack_name, region):
    cf = boto3.client('cloudformation', region_name=region)
    stacks = cf.list_stacks()['StackSummaries']
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if stack_name == stack['StackName']:
            return True
    return False

def stackset_exists(stackset_name):
    cf = boto3.client('cloudformation')
    stacksets = cf.list_stack_sets()['Summaries']
    for stackset in stacksets:
        if stackset['Status'] == 'DELETED':
            continue
        if stackset_name == stackset['StackSetName']:
            return True
    return False