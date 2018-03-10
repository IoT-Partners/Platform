# Internet of Partners Cloud Platform

This repository is an [**AWS Chalice**](https://github.com/aws/chalice) project that automates the creation of a Serverless platform. It creates the AWS Lambda, AWS Gateway and AWS Roles necessary to create the platform.

[This](https://d8dsx2bkn9.execute-api.eu-west-1.amazonaws.com/api/) is the internal url. 

![Alt text](IoT_Partners_Serverless_Platform.png?raw=true "Serverless Architecture")
[Architecture Diagram](https://cloudcraft.co/view/8ad8f0b4-a6b4-4d8c-bcf2-fd2183804bef?key=FVEx48k-viBNqfo7fmSkiw)

## Working with Chalice

### Setting up AWS CLI

```commandline
 $ aws configure --profile iot-partners
 AWS Access Key ID [None]: AKIAJG7SD45V########
 AWS Secret Access Key [None]: Tmc0K0o+OF5Y0Dfecwg4#############
 Default region name [None]: eu-west-1  
 Default output format [None]: json
 
 $ aws ec2 describe-instances --profile iot-partners
 {
     "Reservations": []
 }
 
 $ export AWS_PROFILE=iot-partners
 $ aws s3 ls
 2017-09-27 10:36:04 iotpartners.billing.reports
```

### Setting up AWS Chalice
For Chalice you need to use Python 3.6:
```commandline
 $ sudo port install python36
 $ sudo port select --set python python36
```

Creating virtual environment
```commandline
 $ python -m virtualenv chalice-env
 $ source chalice-env/bin/activate
```

And finally install AWS Chalice
```commandline
 $ pip install chalice
```
Or 
```commandline
 $ sudo python -m pip install -U chalice
```

### Using AWS Chalice
Deploying our project:
```commandline
$ chalice deploy
Creating role: platform-dev
Creating deployment package.
Creating lambda function: platform-dev
Initiating first time deployment.
Deploying to API Gateway stage: api
https://q0gxu5rs7h.execute-api.eu-west-1.amazonaws.com/api/
```
Checking AWS logs:
```commandline
$ chalice logs
2017-11-30 15:45:51.782000 5da9e1 platform - DEBUG - This call is from the Lambda
2017-11-30 15:45:52.020000 5da9e1 platform - DEBUG - print: Data persisted
```
Running it locally:
```commandline
$ chalice local
Serving on localhost:8000
```
Generating a JavaScript SDK to be used easily from the UI:
```commandline
chalice generate-sdk --sdk-type javascript ./ui/sdk/
```
Deleting all your services:
```commandline
$ chalice delete
Deleting rest API q0gxu5rs7h
Deleting lambda function: platform-dev
Deleting cloud watch events
Delete the role platform-dev? [y/N]: y
Deleting role name helloworld-dev
```

### Using Unittest
```commandline
$ pip install unittest2
$ python -m unittest 
```

### Querying DynamoDB ###
Some useful links:
* [Best Practices for DynamodDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices.html)
* [Working with Scans](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Scan.html) 
* [Scans ConditionExpressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)
* [Choosing the Right DynamoDB Partition Key](https://aws.amazon.com/es/blogs/database/choosing-the-right-dynamodb-partition-key/)

Counting all items at DeviceData
```commandline
aws dynamodb scan --table-name DeviceData --select "COUNT"
```

Getting all elements that had the extended Keep Alive
```commandline
aws dynamodb scan 
     --table-name DeviceData 
     --filter-expression "attribute_exists(ka)"
```

