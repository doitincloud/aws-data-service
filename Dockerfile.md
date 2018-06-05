# Notes for Docker Operations

## Step 1. Prepare s3-upload folder
<pre>
cp ../spring-data-service/target/server-1.0.0.jar deployment/lib
</pre>

## Step 2. Build and Publish Image (optional)

<pre>
docker image build -t awsutils .

docker image tag awsutils:latest samwen2017/awsutils:latest

docker login

docker push samwen2017/awsutils:latest
</pre>

## Step 3. Use the Docker Image

<pre>
mkdir WORK_SPACE_DIRECTORY

cd WORK_SPACE_DIRECTORY

export WORKSPACE=$(pwd)

docker run -it --rm --name=awsutls -v ${WORKSPACE}/.aws:/root/.aws -v ${WORKSPACE}:/workspace samwen2017/awsutils sh
</pre>
