# AWS Data Service

This project uses AWS Cloud Formation templates and AWS CLI scripts to deploy server-1.0.0.jar (the product of <a href="https://github.com/samw2017/spring-data-service">Spring Data Service</a>) into AWS cloud. It features with high availability, load balance, auto scaling, code deploy and cloud watch etc.

<img width="768" alt="aws-data-service" src="https://user-images.githubusercontent.com/24588196/29668209-53b022a6-88ad-11e7-8143-6598f3dcb528.png">

## Step 1. Setup AWS Credentials and DevOps Environment

If you are not admin of your AWS account, I assume you have PowerUserAccess permissions. You will need to ask your admin to add permission policy statements in file <a href="https://github.com/samw2017/aws-data-service/blob/master/iam-Dataservice.json">iam-Dataservice.json</a> to your account. It allows cloud formation and aws cli scripts to work on your behalf.

Please have your AWS Access Key ID and AWS Secret Access Key ready.

I use Docker as DevOps environment. My Docker version is 17.06.0-ce. To install Docker, please refer to www.docker.com.

For how the Docker image is built, you can check <a href="https://github.com/samw2017/aws-data-service/blob/master/Dockerfile.md">Dockerfile.md</a> and <a href="https://github.com/samw2017/aws-data-service/blob/master/Dockerfile">Dockerfile</a>.

<pre>

mkdir WORK_SPACE_DIRECTORY

cd WORK_SPACE_DIRECTORY

export WORKSPACE=$(pwd)

# It will download Docker image from hub.docker.com and run it. 
#
docker run -it --rm --name=awsutls -v ${WORKSPACE}/.aws:/root/.aws -v ${WORKSPACE}:/workspace samwen2017/awsutils sh

# we are inside the docker instance now

git clone https://github.com/samw2017/aws-data-service.git

cd aws-data-service

# setup aws credentials, only needed to run once
aws configure
AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID 
AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY_
Default region name [None]: us-east-1
Default output format [None]: json
</pre>

## Step 2. Launch Data Service

<pre>
# launch everthing as default, it takes about 10 minutes.
# You will need to provide an email address for notification of events
#
utils/launch

EMail address to notify if there are any operation events: XXXXXXXXX
create stack resources in progress ...........................................................
CREATE_COMPLETE
create stack database in progress ..................................................................................................................
CREATE_COMPLETE
package and upload to s3 bucket
create stack dataservice in progress ..........................................................................
CREATE_COMPLETE
Done!

URL: http://DataserviceLoadBalancer-XXXXXXXXX.us-east-1.elb.amazonaws.com/ds/v1

</pre>
<details><summary>See a running in detail</summary>
<pre>
utils/launch -vvv


run: cp resources/parameters.json tmp/resources-parameters.json
run: aws configure get region
run: aws ec2 describe-security-groups --query 'SecurityGroups[0].OwnerId' --output text
run: aws sns list-topics

EMail address to notify if there are any operation events: EMAIL-ADDRESS
run: aws ec2 describe-key-pairs
run: aws ec2 create-key-pair --key-name dskey
ssh key: .ssh/dskey-us-east-1-XXXXXXXXXXX.pem
run: aws ec2 describe-security-groups --group-names "Dataservice Default"
run: curl -s https://api.ipify.org?format=json
run: aws ec2 describe-vpcs --filters "Name=isDefault,Values=true"
run: aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxxxxxxxx"
run: aws s3api list-buckets
run: aws iam list-roles
run: aws iam list-instance-profiles
run: aws iam list-roles
run: aws deploy list-applications
{
    "CodeDeployAppName": "",
    "CodeDeployRoleArn": "",
    "DefaultSecurityGroup": "",
    "EMail": "EMAIL-ADDRESS",
    "InstanceProfile": "",
    "InstanceRole": "",
    "KeyName": "dskey",
    "NotificationTopic": "",
    "S3Bucket": "",
    "SSHLocation": "MY-IP-ADDRESSS/32",
    "Subnets": "subnet-xxxxxxxxx, subnet-xxxxxxxxx",
    "VpcId": "vpc-xxxxxxxxx"
}
run: aws cloudformation create-stack --stack-name resources --disable-rollback --capabilities "CAPABILITY_IAM" "CAPABILITY_NAMED_IAM" --template-body file://resources/resources.yaml --tags file://resources/tags.json --parameters file://tmp/resources-parameters.json
call: "aws cloudformation describe-stacks --stack-name resources" every 15 seconds
create stack resources in progress ...........................................................
CREATE_COMPLETE
run: aws cloudformation create-stack --stack-name database --disable-rollback --template-body file://database/ec2-mysql.yaml --tags file://database/tags.json
call: "aws cloudformation describe-stacks --stack-name database" every 15 seconds
create stack database in progress .................................................
CREATE_COMPLETE
run: cp -f tmp/configure.text deployment/configure
run: aws s3 sync s3-upload/packages s3://dataservice-us-east-1-XXXXXXXXXXX/packages --exclude '.*'
package and upload to s3 bucket
run: rm -f s3-upload/deployment/cd-install.zip
run: cd deployment; zip -rq ../s3-upload/deployment/cd-install.zip . -x '.*'; cd ..
run: aws s3 sync s3-upload/deployment s3://dataservice-us-east-1-XXXXXXXXXXX/deployment --exclude '.*'
run: aws cloudformation create-stack --stack-name dataservice --disable-rollback --template-body file://dataservice/autoscaling-elastic-loadbalance-codedeploy.yaml --tags file://dataservice/tags.json
call: "aws cloudformation describe-stacks --stack-name dataservice" every 15 seconds
create stack dataservice in progress .........................................................................................
CREATE_COMPLETE
run: aws deploy get-deployment-group --application-name Dataservice-CD --deployment-group-name Dataservice-CDG-Update
run: cp dataservice/Dataservice-CDG-Update.json tmp/
run: aws deploy create-deployment-group --cli-input-json file://tmp/Dataservice-CDG-Update.json
run: mv tmp/*.json tmp/YYYYMMDD-HHMMSS
run: mv tmp/*.text tmp/YYYYMMDD-HHMMSS
Done!

URL: http://DataserviceLoadBalancer-XXXXXXXXX.us-east-1.elb.amazonaws.com/ds/v1
</pre>
</details>
<br>

Check your email for Dataservice - AWS Notification, click on Confirm subscription.

<pre>
# The AWS Data Service is launched, let's check it
#
curl http://DataserviceLoadBalancer-XXXXXXXXXX.us-east-1.elb.amazonaws.com/ds/v1

# For advanced usage:
#
utils/launch -h
usage: launch [-h] [-v] [--jar jarfile] [--email email] [--host hostname] [--user username] [--passwd password]

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      show running details
  --jar jarfile      jar file to run, must already in deployment/lib folder
  --email email      email address to notify for operation events
  --host hostname    database host domain name or ip
  --user username    user name for accessing database
  --passwd password  user password for accessing database

if database host, user and password are provided, launch will skip the database cloud formation stack:

utils/update --host DB_HOST_NAME --user DB_USER_NAME --passwd DB_USER_PASS

</pre>

## Step 3. Update with Code Deploy and Put It in Production

<pre>
# run update with default, it takes about 7 minutes. Most of the minutes are used for 
# BlockTraffic and AllowTraffic lifecycle events. 

utils/update
package and upload to s3 bucket
deploy d-XXXXXXXXXX in progress ................................................................................................................................................
Succeeded

</pre>

<details><summary>See a running in detail</summary>
<p>
<pre>
utils/update -vvv --jar server-1.0.1.jar

run: aws cloudformation describe-stacks --stack-name resources
run: aws cloudformation describe-stacks --stack-name database
run: cp -f tmp/configure.text deployment/configure
package and upload to s3 bucket
run: rm -f s3-upload/deployment/cd-update.zip
run: cd deployment; zip -rq ../s3-upload/deployment/cd-update.zip . -x '.*'; cd ..
run: aws configure get region
run: aws ec2 describe-security-groups --query 'SecurityGroups[0].OwnerId' --output text
run: aws s3 sync s3-upload/deployment s3://dataservice-us-east-1-XXXXXXXXXXX/deployment --exclude '.*'
run: aws cloudformation describe-stacks --stack-name dataservice
run: aws deploy get-deployment-group --application-name Dataservice-CD --deployment-group-name Dataservice-CDG-Update
run: aws deploy create-deployment --application-name Dataservice-CD --s3-location bucket=dataservice-us-east-1-XXXXXXXXXXX,key=deployment/cd-update.zip,bundleType=zip --deployment-group-name Dataservice-CDG-Update --file-exists-behavior OVERWRITE --description "Dataservice Deployment at 20170829-151551"
call: "aws deploy get-deployment --deployment-id d-XXXXXXXXX" every 15 seconds
deploy d-XXXXXXXXX in progress ................................................................................................................................................
Succeeded
run: aws s3 cp s3://dataservice-us-east-1-XXXXXXXXXXX/deployment/cd-update.zip s3://dataservice-us-east-1-XXXXXXXXXXX/deployment/cd-install.zip
run: aws s3 rm s3://dataservice-us-east-1-XXXXXXXXXXX/deployment/cd-update.zip
run: mv tmp/*.json tmp/YYYYMMDD-HHMMSS
run: mv tmp/*.text tmp/YYYYMMDD-HHMMSS
</pre>
</p>
</details>
<br>

<pre>
# For advanced usage:
#
utils/update -h
usage: update [-h] [-v] [--group group] [--jar jarfile] [--host hostname] [--user username] [--passwd password]

optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      show running details
  --group group      deployment group name, the json file must already in dataservice folder
  --jar jarfile      jar file to run, must already in deployment/lib folder
  --host hostname    database host domain name or ip
  --user username    user name for accessing database
  --passwd password  user password for accessing database


Here is a short version tree view of deployment folder:
 
deployment
├── appspec.yml
├── bin
    ...
├── configure
├── lib
│   └── server-1.0.0.jar
...

A) If we have a new version of the jar file, put the new jar in deployment/lib folder:

utils/update --jar NEW.jar

B) If use a different database:

utils/update --host DB_HOST_NAME --user DB_USER_NAME --passwd DB_USER_PASS

then, shutdown the database instance lauched by cloud formation stack.

C) If put it in product, for security reason, modify file 
   dataservice/autoscaling-elastic-loadbalance-codedeploy.yaml:

Change LoadBalancer Scheme from internet-facing to internal

# for test and demo 
#      Scheme: internet-facing
# for prodouction 
      Scheme: internal

delete dataservice stack and run utils/launch again,
</pre>

## Step 4. AWS Console Checks/Shutdown/Cleanup AWS Resources

<a href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1">Check Cloud Formation</a>

<a href="https://console.aws.amazon.com/ec2/v2/home?region=us-east-1">Check EC2 Instances</a>

<a href="https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LoadBalancers:">Check Load Balancer</a>

<a href="https://console.aws.amazon.com/ec2/autoscaling/home?region=us-east-1">Check Autoscaling<a/>

<a href="https://s3.console.aws.amazon.com/s3/home?region=us-east-1">Check S3</a>

<a href="https://console.aws.amazon.com/codedeploy/home?region=us-east-1#/applications">Check Code Deploy</a>

<a href="https://console.aws.amazon.com/codedeploy/home?region=us-east-1#/deployments">Check Deployments</a>

<pre>
# It takes about 5 minutes.
#
utils/cleanup

# Cleanup everthings.
#
utils/cleanup --all 
</pre>

<details><summary>See a running in detail</summary>
<pre>
utils/cleanup -vvv


run: aws cloudformation delete-stack --stack-name dataservice
call: "aws cloudformation describe-stacks --stack-name dataservice" every 15 seconds
delete stack dataservice in progress ......................................................
NOT_EXISTS
run: aws cloudformation delete-stack --stack-name database
call: "aws cloudformation describe-stacks --stack-name database" every 15 seconds
delete stack database in progress .............................
NOT_EXISTS
run: aws deploy delete-deployment-group --application-name Dataservice-CD --deployment-group-name Dataservice-CDG-Update
run: aws cloudformation delete-stack --stack-name resources
call: "aws cloudformation describe-stacks --stack-name resources" every 15 seconds
delete stack resources in progress ....
NOT_EXISTS
run: mv tmp/*.json tmp/YYYYMMDD-HHMMSS
run: mv tmp/*.text tmp/YYYYMMDD-HHMMSS
</pre>
</details>