##
# Copyright 2017 Sam Wen.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

import sys
import os
import json
import glob
import filecmp
import time
import argparse
from argparse import RawTextHelpFormatter
from validate_email import validate_email

verbose = 0

#############################################################################################
# help functions

# get configure from command line arguments for launch
#
def launch_parse_args(config):

    global verbose

    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50, width=120)
    parser = argparse.ArgumentParser(formatter_class=formatter_class)

    parser.add_argument('-v', '--verbose', help='show running details', action='count', default=1)
    parser.add_argument('--jar', metavar='jarfile', help='jar file to run, must already in deployment/lib folder')
    parser.add_argument('--email', metavar='email', help='email address to notify for operation events', action="store")
    parser.add_argument('--host', metavar='hostname', help='database host domain name or ip')
    parser.add_argument('--user', metavar='username', help='user name for accessing database')
    parser.add_argument('--passwd', metavar='password', help='user password for accessing database')

    args = parser.parse_args()

    verbose = args.verbose
    config['verbose'] = verbose

    if not args.email == None:
        if not validate_email(args.email):
            print('Invalid email address!')
            sys.exit(1)
        else:
            config['email'] = args.email
        
    if not args.jar == None:
        jar_filepath = 'deployment/lib/'+args.jar
        if not os.path.exists(jar_filepath):
            print(jar_filepath + ' not exists!')
            sys.exit(1)
        else:
            config['JAR_FILE'] = args.jar

    if not args.host == None:
        config['DB_HOST_NAME'] = args.host

    if not args.user == None:
        config['DB_USER_NAME'] = args.user

    if not args.passwd == None:
        config['DB_USER_PASS'] = args.passwd

# get configure from command line arguments for update
#
def update_parse_args(config):

    global verbose

    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50, width=120)
    parser = argparse.ArgumentParser(formatter_class=formatter_class)

    parser.add_argument('-v', '--verbose', help='show running details', action='count', default=1)
    parser.add_argument('--group', metavar='group', help='deployment group name, the json file must already in dataservice folder',\
        default='Dataservice-CDG-Update')
    parser.add_argument('--jar', metavar='jarfile', help='jar file to run, must already in deployment/lib folder')
    parser.add_argument('--host', metavar='hostname', help='database host domain name or ip')
    parser.add_argument('--user', metavar='username', help='user name for accessing database')
    parser.add_argument('--passwd', metavar='password', help='user password for accessing database')

    args = parser.parse_args()

    verbose = args.verbose
    config['verbose'] = verbose

    update_filepath = 'dataservice/'+args.group+'.json'
    if not os.path.exists(update_filepath):
        print(update_filepath + ' not exists!')
        sys.exit(1)
    else:
        config['update_group'] = args.group
        
    if not args.jar == None:
        jar_filepath = 'deployment/lib/'+args.jar
        if not os.path.exists(jar_filepath):
            print(jar_filepath + ' not exists!')
            sys.exit(1)
        else:
            config['JAR_FILE'] = args.jar

    if not args.host == None:
        config['DB_HOST_NAME'] = args.host

    if not args.user == None:
        config['DB_USER_NAME'] = args.user

    if not args.passwd == None:
        config['DB_USER_PASS'] = args.passwd

# get configure from command line arguments for cleanup
#
def cleanup_parse_args(config):

    global verbose

    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50, width=120)
    parser = argparse.ArgumentParser(formatter_class=formatter_class)

    parser.add_argument('-v', '--verbose', help='show running details', action='count', default=1)
    parser.add_argument('--all', help='cleanup s3 bucket and retained resources', action='store_true')

    args = parser.parse_args()

    verbose = args.verbose
    config['verbose'] = verbose

    return args.all

# run cmd and return exit code
#
def run_exit_code(cmd, filename):

    global verbose

    if verbose > 2:
        print('run: ' + cmd)

    if filename != '':
        cmd = cmd + ' > ' + filename + ' 2>&1'
    else:
        cmd = cmd + ' > /dev/null 2>&1'

    ret = os.system(cmd)

    return os.WEXITSTATUS(ret)

# run cmd and if exit code not 0 exit the program
#
def run(cmd, filename):
    
    exit_code = run_exit_code(cmd, filename)
    
    if exit_code != 0:
        print('Failed!')
        if filename != '':
            with open(filename, 'r') as data_file:
                for line in data_file.readlines():
                    print(line)
        sys.exit(exit_code)

    return

# get dict data type from parameters array
#
def get_parameters(jsonfile):

    with open(jsonfile) as data_file:
        parameters = json.load(data_file)
        
    params = {}
    i = 0
    while i < len(parameters):
        parameter = parameters[i]
        params[parameter['ParameterKey']] = parameter['ParameterValue']
        i += 1

    return params

# check stact status 
#
def check_stack(stack_name):

    jsonfile = 'tmp/' + stack_name + '-result.json'
    cmd = 'aws cloudformation describe-stacks --stack-name ' + stack_name + ' > ' + jsonfile + ' 2>&1'

    ret = os.system(cmd)

    exit_code = os.WEXITSTATUS(ret)

    if exit_code != 0:
        ret = 'NOT_EXISTS'
    else:
        with open(jsonfile) as data_file:
            data = json.load(data_file)
        if len(data['Stacks']) == 0:
            ret = 'NOT_EXISTS'
        else:
            ret = data['Stacks'][0]['StackStatus']

    return ret

# create stack
#
def create_stack(stack_name, template, iam):

    global verbose

    stack_status = check_stack(stack_name)

    if stack_status == 'NOT_EXISTS':

        jsonfile = 'tmp/' + stack_name + '-cmd.json'
        cmd  = 'aws cloudformation create-stack --stack-name ' + stack_name + ' --disable-rollback'
        if iam:
           cmd  += ' --capabilities "CAPABILITY_IAM" "CAPABILITY_NAMED_IAM"'
        cmd += ' --template-body file://' + stack_name + '/' + template
        cmd += ' --tags file://' + stack_name + '/tags.json'
        params_file = stack_name + '-parameters.json'
        if os.path.exists('./tmp/' + params_file):
            cmd += ' --parameters file://tmp/' + params_file

        run(cmd, jsonfile)

        stack_status = 'CREATE_IN_PROGRESS'

    if stack_status == 'CREATE_IN_PROGRESS':

        if verbose > 2:
            print('call: "aws cloudformation describe-stacks --stack-name '+stack_name+'" every 15 seconds')
        if verbose > 0:
            print('create stack '+stack_name+' in progress ', end='')
        sys.stdout.flush()
        i = 0
        while True:
            i = i + 1
            time.sleep(3)
            if i % 5 == 0:
                stack_status = check_stack(stack_name)
                if stack_status != 'CREATE_IN_PROGRESS':
                    break
            if verbose > 0:
                print('.', end='')
                sys.stdout.flush()

        if verbose > 0:
            print()
            sys.stdout.flush()

        if stack_status != 'CREATE_COMPLETE':
            with open (jsonfile, 'r') as text_file:
                for line in text_file:
                    print(line)

    if verbose > 0:
        print(stack_status)

    return stack_status

# delete stack
#
def delete_stack(stack_name, stack_status):

    global verbose

    if stack_status != 'DELETE_IN_PROGRESS':
        jsonfile = 'tmp/' + stack_name + '-delete.json'
        cmd  = 'aws cloudformation delete-stack --stack-name ' + stack_name
        run(cmd, jsonfile)

    if verbose > 2:
        print('call: "aws cloudformation describe-stacks --stack-name '+stack_name+'" every 15 seconds')
    if verbose > 0:
        print('delete stack '+stack_name+' in progress ', end='')
    sys.stdout.flush()
    i = 0
    while True:
        i = i + 1
        time.sleep(3)
        if i % 5 == 0:
            stack_status = check_stack(stack_name)
            if stack_status != 'DELETE_IN_PROGRESS':
                break
        if verbose > 0:
            print('.', end='')
            sys.stdout.flush()

    if verbose > 0:
        print()
        sys.stdout.flush()
        print(stack_status)

    return stack_status

# get region
#
def get_region():

    regionfile = 'tmp/region.text'
    if not os.path.exists(regionfile):
        cmd = 'aws configure get region'
        run(cmd, regionfile)
    with open(regionfile) as data_file:
        region = data_file.readline().strip()
    return region;

# get account id
#
def get_account_id():
    
    accountfile = 'tmp/account.text'
    if not os.path.exists(accountfile):
        cmd = 'aws ec2 describe-security-groups --query \'SecurityGroups[0].OwnerId\' --output text'
        run(cmd, accountfile)
    with open(accountfile) as data_file:
        account_id = data_file.readline().strip()
    return account_id

# get database settings
#
def get_config_database_settings(config):
    
    stack_name = 'database'
    jsonfile = 'tmp/database-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name database'
        run(cmd, jsonfile)
    with open(jsonfile) as data_file:
        data = json.load(data_file)
        for output in data['Stacks'][0]['Outputs']: 
            if output['OutputKey'] == 'DBHostName':
                config['DB_HOST_NAME'] = output['OutputValue']
            if output['OutputKey'] == 'DBUserName':
                config['DB_USER_NAME'] = output['OutputValue']
            if output['OutputKey'] == 'DBUserPass':
                config['DB_USER_PASS'] = output['OutputValue']

# make config file
#
def make_config_file(config, configfile):

    if not 'S3_BUCKET' in config:
        config['S3_BUCKET'] = get_s3_bucket()
    
    if not 'DB_HOST_NAME' in config  or \
       not 'DB_USER_NAME' in config or \
       not 'DB_USER_PASS' in config:
        get_config_database_settings(config)

    tmpfile = 'tmp/configure.text'
    with open(tmpfile, 'w') as data_file:
        for key, value in config.items():
            data_file.write('export ' + key + '=' + value + '\n')
    
    if os.path.exists(configfile):
        if filecmp.cmp(configfile, tmpfile):
            return

    cmd = 'cp -f ' + tmpfile + ' ' + configfile
    run(cmd, '')


# package and upload to s3 bucket 
#
def package_and_upload_to_s3_bucket(filename):

    global verbose

    if verbose > 0:
        print('package and upload to s3 bucket')

    deploy_file = 's3-upload/deployment/'+filename+'.zip'

    #check if need to regenerate deployment file
    if os.path.exists(deploy_file):
        deploy_file_ctime = os.path.getctime(deploy_file)
        files = sorted(glob.iglob('deployment/**',  recursive=True), key=os.path.getctime, reverse=True)
        latest_ctime = os.path.getctime(files[0])
        if latest_ctime >= deploy_file_ctime:
            cmd = 'rm -f ' + deploy_file 
            run(cmd, '')

    if not os.path.exists(deploy_file):
        cmd = 'cd deployment; zip -rq ../'+deploy_file+' . -x \'.*\'; cd ..' 
        run(cmd, '')

    # sync deployment folder with s3 bucket
    s3_bucket = get_s3_bucket()
    resultfile = 'tmp/s3-upload-out.text'
    cmd = 'aws s3 sync s3-upload/deployment s3://'+s3_bucket+'/deployment --exclude \'.*\''
    run(cmd, resultfile)

# get s3 bucket name
#
def get_s3_bucket():

    exit_code = 1
    jsonfile = 'tmp/resources-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name resources'
        exit_code = run_exit_code(cmd, jsonfile)

    if exit_code == 0:
        with open(jsonfile) as data_file:
            data = json.load(data_file)
            for output in data['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'S3Bucket':
                    return output['OutputValue']
    else:
        region = get_region()
        account_id = get_account_id()
        return 'dataservice-'+region+'-'+account_id

# get code deploy application name
#
def get_cd_appname():

    jsonfile = 'tmp/resources-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name resources'
        run(cmd, jsonfile)
    with open(jsonfile) as data_file:
        data = json.load(data_file)
        for output in data['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'CodeDeployAppName':
                return output['OutputValue']

# make update deployment group
#
def make_update_deployment_group(group_name):

    jsonfile = 'tmp/resources-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name resources'
        run(cmd, jsonfile)
    with open(jsonfile) as data_file:
        data = json.load(data_file)
        for output in data['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'S3Bucket':
                s3_bucket = output['OutputValue']
            if output['OutputKey'] == 'CodeDeployAppName':
                cd_appname = output['OutputValue']
            if output['OutputKey'] == 'CodeDeployRoleArn':
                cd_role_arn = output['OutputValue']
            if output['OutputKey'] == 'NotificationTopic':
                sns_topic_arn = output['OutputValue']

    jsonfile = 'tmp/dataservice-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name dataservice'
        run(cmd, jsonfile)
    with open(jsonfile) as data_file:
        data = json.load(data_file)
        for output in data['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'AutoScalingGroup':
                autoscaling_group = output['OutputValue']
            if output['OutputKey'] == 'LoadBalanceTargetGroup':
                target_group = output['OutputValue']

    # check if we already have it
    #
    jsonfile = 'tmp/deployment-group-update.json'
    cmd = 'aws deploy get-deployment-group --application-name ' + \
        cd_appname+' --deployment-group-name ' + group_name
        
    exit_code = run_exit_code(cmd, jsonfile)
    
    if exit_code == 0:
        with open(jsonfile) as data_file:
            data = json.load(data_file)
        data = data['deploymentGroupInfo']
        if data['applicationName'] == cd_appname and \
           data['deploymentGroupName'] == group_name and \
           data['autoScalingGroups'][0]['name'] == autoscaling_group and \
           data['serviceRoleArn'] == cd_role_arn and \
           data['triggerConfigurations'][0]['triggerTargetArn'] == sns_topic_arn:
           return

        cmd = 'aws deploy delete-deployment-group --application-name ' + \
        cd_appname+' --deployment-group-name ' + group_name
        run_exit_code(cmd, '')

    jsonfile = 'tmp/' + group_name + '.json'
    if not os.path.exists(jsonfile):
        cmd = 'cp dataservice/' + group_name + '.json tmp/'
        run(cmd, '')

    with open(jsonfile) as data_file:
        data = json.load(data_file)

    data['applicationName'] = cd_appname
    data['deploymentGroupName'] = group_name
    data['autoScalingGroups'][0] = autoscaling_group
    data['serviceRoleArn'] = cd_role_arn
    data['triggerConfigurations'][0]['triggerTargetArn'] = sns_topic_arn

    with open(jsonfile, 'w') as data_file:
        data_file.write(json.dumps(data, indent=4, sort_keys=True))

    cmd = 'aws deploy create-deployment-group --cli-input-json file://'+jsonfile
    
    resultfile = '/tmp/create-deployment-group.json'
    run(cmd, resultfile)

# make update deployment group
#
def remove_update_deployment_group(group_name):

    jsonfile = 'tmp/resources-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name resources'
        run(cmd, jsonfile)
    with open(jsonfile) as data_file:
        data = json.load(data_file)
        for output in data['Stacks'][0]['Outputs']:
            if output['OutputKey'] == 'CodeDeployAppName':
                cd_appname = output['OutputValue']

    cmd = 'aws deploy delete-deployment-group --application-name ' + \
        cd_appname+' --deployment-group-name ' + group_name
    
    run_exit_code(cmd, '')
    
# check deployment in progress status
#
def check_deploy_in_progress(deployment_id):

    global verbose

    jsonfile='tmp/deploy-status.json'
    cmd = 'aws deploy get-deployment --deployment-id '+deployment_id

    if verbose > 2:
        print('call: "'+cmd+'" every 15 seconds')
    if verbose > 0:
        print('deploy '+deployment_id+' in progress ', end='')
        sys.stdout.flush()
    
    i = 0
    while True:
        i = i + 1
        time.sleep(3)
        if i % 5 == 0:

            ret = os.system(cmd + ' > ' + jsonfile + ' 2>&1')
            exit_code = os.WEXITSTATUS(ret)

            if exit_code != 0:
                print('Failed')
                sys.exit(exit_code)

            with open(jsonfile) as data_file:
                data = json.load(data_file)
                status = data['deploymentInfo']['status']
                if status != 'InProgress':
                    break;

        if verbose > 0:
            print('.', end='')
            sys.stdout.flush()

    if verbose > 0:
        print()
        sys.stdout.flush()
        print(status)

    if status != 'Succeeded':
        if 'errorInformation' in data['deploymentInfo']:
            print(json.dumps(data['deploymentInfo']['errorInformation'], indent=4, sort_keys=True))

    return status

def delete_s3_bucket():

    if verbose > 0:
        print('delete s3 bucket')

    s3_bucket = get_s3_bucket()
    jsonfile = 'tmp/object-versions.json'
    cmd = 'aws s3api list-object-versions --bucket '+s3_bucket
    exit_code = run_exit_code(cmd, jsonfile)

    if exit_code == 0 and os.path.getsize(jsonfile) > 0:
        with open(jsonfile) as data_file:
            data = json.load(data_file)
        for version in data['Versions']:
            key = version['Key']
            version_id = version['VersionId']
            cmd='aws s3api delete-object --bucket '+s3_bucket+' --key '+key+' --version-id '+version_id
            run(cmd, '')
        for version in data['DeleteMarkers']:
            key = version['Key']
            version_id = version['VersionId']
            cmd='aws s3api delete-object --bucket '+s3_bucket+' --key '+key+' --version-id '+version_id
            run(cmd, '')

    cmd = 'aws s3 rb s3://'+s3_bucket+' --force'
    run_exit_code(cmd, '')

def delete_retained_resources():

    if verbose > 0:
        print('delete retained resources')

    default_security_group = 'Dataservice Default'
    sshkey = 'dskey'
    instance_role_name = 'Dataservice-EC2-Role'
    instance_profile_name = 'Dataservice-EC2-Profile'
    cd_appname = 'Dataservice-CD'

    region = get_region()
    account_id = get_account_id()
    sns_topic_arn = 'arn:aws:sns:'+region+':'+account_id+':Dataservice'

    deploy_role_name = 'Dataservice-CodeDeploy-Role'
    deploy_policy_name = 'CodeDeployPolicy'
    instance_policy_name = 'InstanceRolePolicy'

    exit_code = 1
    jsonfile = 'tmp/resources-result.json'
    if not os.path.exists(jsonfile):
        cmd = 'aws cloudformation describe-stacks --stack-name resources'
        exit_code = run_exit_code(cmd, jsonfile)

    if exit_code == 0:
        with open(jsonfile) as data_file:
            data = json.load(data_file)
            for output in data['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'DefaultSecurityGroup':
                     default_security_group = output['OutputValue']
                if output['OutputKey'] == 'KeyName':
                     sshkey = output['OutputValue']
                if output['OutputKey'] == 'InstanceRole':
                     instance_role_name = output['OutputValue']
                if output['OutputKey'] == 'InstanceProfile':
                     instance_profile_name = output['OutputValue']
                if output['OutputKey'] == 'CodeDeployAppName':
                    cd_appname = output['OutputValue']
                if output['OutputKey'] == 'NotificationTopic':
                    sns_topic_arn = output['OutputValue']

    cmd = 'aws ec2 delete-security-group --group-name "'+default_security_group+'"'
    run_exit_code(cmd, '')
    
    cmd = 'aws ec2 delete-key-pair --key-name '+sshkey
    run_exit_code(cmd, '')

    cmd = 'aws iam delete-role-policy --role-name '+deploy_role_name+' --policy-name '+deploy_policy_name
    run_exit_code(cmd, '')

    cmd = 'aws iam delete-role --role-name '+deploy_role_name
    run_exit_code(cmd, '')

    cmd = 'aws iam delete-role-policy --role-name '+instance_role_name+' --policy-name '+instance_policy_name
    run_exit_code(cmd, '')

    cmd = 'aws iam remove-role-from-instance-profile --instance-profile-name '+instance_profile_name+' --role-name '+instance_role_name
    run_exit_code(cmd, '')

    cmd = 'aws iam delete-role --role-name '+instance_role_name
    run_exit_code(cmd, '')

    cmd = 'aws iam delete-instance-profile --instance-profile-name '+instance_profile_name
    run_exit_code(cmd, '')

    cmd = 'aws sns delete-topic --topic-arn '+sns_topic_arn
    run_exit_code(cmd, '')

    cmd = 'aws deploy delete-application --application-name '+cd_appname
    run_exit_code(cmd, '')

# prepare parameters for resources stack
#
def prepare_parameters(argv_email):

    global verbose

    stack_name = 'resources'

    std_params = get_parameters(stack_name + '/parameters.json')

    # prepare ./tmp/${stack_name}-parameters.json
    #
    if not os.path.exists('tmp/' + stack_name + '-parameters.json'):
        cmd = 'cp ' + stack_name + '/parameters.json ' + \
          'tmp/' + stack_name + '-parameters.json'
        run(cmd, '')

    params = get_parameters('tmp/' + stack_name + '-parameters.json')

    region = get_region()
    account_id = get_account_id()

    # setup NotificationTopic
    #
    key = 'NotificationTopic'
    if params[key] != '' and params[key] != std_params[key]:
        notification_topic = params[key]
    else:
        # get existing NotificationTopic
        notification_topic = ''
        jsonfile = 'tmp/topics.json'
        cmd = 'aws sns list-topics'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        for topic in data['Topics']:
            if topic['TopicArn'].endswith(':Dataservice'):
                notification_topic = topic['TopicArn']
                break

        params[key] = notification_topic

    # setup email if notification_topic not exists
    #
    key = 'EMail'
    if notification_topic == '':
        if argv_email != '':
            email = argv_email
            params[key] = email
        elif params[key] != '' and params[key] != std_params[key]:
            email = params[key]
        else:
            # get email from console input
            email = ''
            jsonfile = 'tmp/input.json'
            if os.path.exists(jsonfile):
                with open(jsonfile) as data_file:
                    data = json.load(data_file)
                if 'EMail' in data:
                    email = data['EMail']
            else:
                data = {}
            
            if email == '':
                prompt = '\nEMail address to notify if there are any operation events: '
            else:
                prompt = '\nEMail address to notify if there are any operation events ('+email+'): '

            while True:
                email_input = input(prompt)
                if email_input != '':
                    email = email_input
                if validate_email(email):
                    data['EMail'] = email
                    with open(jsonfile, 'w') as data_file:
                        data_file.write(json.dumps(data, indent=4, sort_keys=True))
                    break
                else:
                    print('Invalid email address!')

            params[key] = email
    else:
        params[key] = 'Skipped'

    # setup ssh key
    #
    key = 'KeyName'
    if params[key] != '' and params[key] != std_params[key]:
        ssh_key = params[key]
    else:
        # get existing dskey key
        ssh_key = ''
        cmd = 'aws ec2 describe-key-pairs'
        jsonfile = 'tmp/key-pairs.json'
        run(cmd, jsonfile)
    
        with open(jsonfile) as data_file:
            data = json.load(data_file)
        for keypair in data['KeyPairs']:
            if keypair['KeyName'] == 'dskey':
                ssh_key = 'dskey'

        if ssh_key == '':
            cmd = 'aws ec2 create-key-pair --key-name dskey'
            jsonfile = 'tmp/dskey.json'
            run(cmd, jsonfile)
            
            ssh_key = 'dskey'
            with open(jsonfile) as data_file:
                data = json.load(data_file)
            ssh_dir = '.ssh'
            os.makedirs(ssh_dir, exist_ok=True)
            filename = ssh_dir + '/' + data['KeyName']+'.pem'
            if os.path.exists(filename):
                filename = ssh_dir + '/' + data['KeyName'] + '-' + region + '-' + account_id + '.pem'
            with open(filename, 'w') as text_file:
                text_file.write(data['KeyMaterial'])
            os.chmod(filename, 0o600) 
            os.remove(jsonfile)
            if verbose > 1:
                print('ssh key: '+filename)

        params[key] = ssh_key

    # setup default security group
    #
    key = 'DefaultSecurityGroup'
    if params[key] != '' and params[key] != std_params[key]:
        default_security_group = params[key]
    else:
        # get pre-existing default security group
        default_security_group = ''
        jsonfile = 'tmp/default-security-group.json'
        cmd = 'aws ec2 describe-security-groups --group-names "Dataservice Default"'
        exit_code = run_exit_code(cmd, jsonfile)

        if exit_code == 0:
            with open(jsonfile) as data_file:
                data = json.load(data_file)
            for security_group in data['SecurityGroups']:
                if security_group['GroupName'] == 'Dataservice Default':
                    default_security_group = security_group['GroupId']
                    break

        params[key] = default_security_group

    # setup ssh location
    # 
    key = 'SSHLocation'
    if params[key] != '' and params[key] != std_params[key]:
        my_ip = params[key]
    else:
        # get my ip
        jsonfile = 'tmp/myip.json'
        cmd = 'curl -s https://api.ipify.org?format=json'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        if 'ip' in data:
            my_ip = data['ip'] + '/32'
        else:
            print('Failed to get my IP address!')
            sys.exit(1)

        params[key] = my_ip

    # setup vpc id
    #
    key = 'VpcId'
    if params[key] != '' and params[key] != std_params[key]:
        vpc_id = params[key]
    else:
        # get the default vpc id
        vpc_id = ''
        jsonfile = 'tmp/vpcs.json'
        cmd = 'aws ec2 describe-vpcs --filters "Name=isDefault,Values=true"'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        if len(data['Vpcs']) > 0:
            vpc_id = data['Vpcs'][0]['VpcId']
        else:
            print('Failed! Default VPC not found.')
            sys.exit(1)

        params[key] = vpc_id

    # setup subnets list
    #
    key = 'Subnets'
    if params[key] != '' and params[key] != std_params[key]:
        subnets = params[key]
    else:
        # get two subnets from the vpc
        subnets = ''
        jsonfile = 'tmp/subnets.json'
        cmd = 'aws ec2 describe-subnets --filters "Name=vpc-id,Values='+vpc_id+'"'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        subnet1 = data['Subnets'][0]['SubnetId']
        subnet2 = data['Subnets'][1]['SubnetId']
        subnets = subnet1 + ', ' + subnet2
        params[key] = subnets

    # setup s3 bucket
    #
    key = 'S3Bucket'
    if params[key] != '' and params[key] != std_params[key]:
        s3_bucket = params[key]
    else:
        # get pre-existing dataservice bucket
        s3_bucket = ''
        jsonfile = 'tmp/buckets.json'
        cmd = 'aws s3api list-buckets'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        target_s3_bucket = 'dataservice-' + region + '-' + account_id
        for bucket in data['Buckets']:
            if bucket['Name'] == target_s3_bucket:
                s3_bucket = target_s3_bucket
                break

        params[key] = s3_bucket

    # setup instance role
    #
    key = 'InstanceRole'
    if params[key] != '' and params[key] != std_params[key]:
        instance_role = params[key]
    else:
        # get pre-existing instance role
        instance_role = ''
        jsonfile = 'tmp/roles.json'
        cmd = 'aws iam list-roles'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        target_instance_role = 'Dataservice-EC2-Role'
        for role in data['Roles']:
            if role['RoleName'] == target_instance_role:
                instance_role = target_instance_role
                break

        params[key] = instance_role

    # setup instance profile
    #
    key = 'InstanceProfile'
    if params[key] != '' and params[key] != std_params[key]:
        instance_profile = params[key]
    elif params['InstanceRole'] != '':
        # get pre-existing instance profile for the role
        instance_profile = ''
        jsonfile = 'tmp/profiles-for-role.json'
        cmd = 'aws iam list-instance-profiles-for-role --role-name ' + params['InstanceRole']
        exit_code = run_exit_code(cmd, jsonfile)

        if exit_code == 0:
            with open(jsonfile) as data_file:
                data = json.load(data_file)
            target_instance_profile = 'Dataservice-EC2-Profile'
            for profile in data['InstanceProfiles']:
                if profile['InstanceProfileName'] == target_instance_profile:
                    instance_profile = target_instance_profile
                    break
                    
        params[key] = instance_profile
    else:
        params[key] = ''

    # delete empty instane profile - Dataservice-EC2-Profile if it exists
    #
    if params['InstanceRole'] == '':
        # get pre-existing instance profiles
        jsonfile = 'tmp/profiles.json'
        cmd = 'aws iam list-instance-profiles'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        instance_profile = 'Dataservice-EC2-Profile'
        for profile in data['InstanceProfiles']:
            if profile['InstanceProfileName'] == instance_profile:
                jsonfile = 'tmp/delete-profile-result.json'
                cmd = 'aws iam delete-instance-profile --instance-profile-name ' + instance_profile
                run(cmd, jsonfile)
                break

    # setup code deploy role Arn
    #
    key = 'CodeDeployRoleArn'
    if params[key] != '' and params[key] != std_params[key]:
        codedeploy_role = params[key]
    else:
        # get pre-existing codedeploy role
        codedeploy_role_arn = ''
        jsonfile = 'tmp/roles.json'
        cmd = 'aws iam list-roles'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        target_codedeploy_role = 'Dataservice-CodeDeploy-Role'
        for role in data['Roles']:
            if role['RoleName'] == target_codedeploy_role:
                codedeploy_role_arn = role['Arn']
                break

        params[key] = codedeploy_role_arn

    # setup code deploy app name
    #
    key = 'CodeDeployAppName'
    if params[key] != '' and params[key] != std_params[key]:
        cd_app_name = params[key]
    else:
        # get pre-existing codedeploy app name
        cd_app_name = ''
        jsonfile = 'tmp/cd-app-names.json'
        cmd = 'aws deploy list-applications'
        run(cmd, jsonfile)

        with open(jsonfile) as data_file:
            data = json.load(data_file)
        target_cd_app_name = 'Dataservice-CD'
        for app_name in data['applications']:
            if app_name == target_cd_app_name:
                cd_app_name = target_cd_app_name
                break

        params[key] = cd_app_name

    # update ./tmp/${stack_name}-parameters.json
    #
    data = []
    for key in params:
        parameter = {
            'ParameterKey' : key,
            'ParameterValue' : params[key]
        }
        data.append(parameter)
    
    jsonfile = 'tmp/' + stack_name + '-parameters.json'

    with open(jsonfile, 'w') as data_file:
       data_file.write(json.dumps(data, indent=4, sort_keys=True))

    return params
