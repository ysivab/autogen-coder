template_constraints = '''
    You must follow all of these rules:
    Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
    Rule #1: Deploy resource using AWS CLI in ca-central-1 region
    Rule #2: You must randomize the resource name to avoid conflicts
    Rule #3: You must identify the lambda code URI and add the link in your CloudFormation. Do not put placeholder or instructions.
    Rule #4: You must only send one codeblock with CloudFormation template. No other codeblock should be there.
'''

resource_constraints_task = '''
    Review the CloudFormation template one resource at a time against the constraints given to you in <constraints></constraints>. Constraints has an entire list. Only look at the constraint applicable to the resource you are reviewing, then analyze the template to ensure all rules are followed. Then repeat this for every resource in the CloudFormation template. Do not add any new resources to the CloudFormation template, just fix the one that's already given to you. 
'''

resource_constraints = {
    "AWS-API-Gateway": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any API Gateway, then DO NOT ADD any API gateway.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
    ''',
    "Lambda": '''
        Each Lambda function code and all dependent libraries are in these folder {json.dumps(self.cloud_stack_map)}
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any Lambda,DO NOT ADD ANY new Lambda.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
        Rule #4: You must ensure Lambda code URI is not a placeholder. Lambda URI will only come from the data given to you in <packages></packages>
        Rule #5: This Lambda will not be deployed inside a VPC
    ''',
    "S3-bucket": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any S3 Bucket,DO NOT ADD ANY new S3 bucket.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
    ''',
    "DynamoDB": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any DynamoDB,DO NOT ADD ANY new DynamoDB.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
        Rule #4: You must review the source code for the Lambdas (given in <source_code>) to double check if all DynamoDB tables are captured in the CloudFormation template
    ''',
    "SSM": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any SSM,DO NOT ADD ANY new SSM.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
        Rule #4: You must review the source code for the Lambdas (given in <source_code>) to ensure all SSM parameters are created
        Rule #5: You must add the SSM parameters that required by the Lambda in the environment variables if necessary
    ''',
    "IAM": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any IAM,DO NOT ADD ANY new IAM.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
        Rule #4: You must review the source code to identify which resources Lambda is expected to access and add the correct IAM policies to ensure Lambda has access to the resource
        Rule #5: You must ensure basic IAM roles and policies required for the Lambda is included for Lambda IAM role
    ''',
    "SecurityGroup": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any Security Group,DO NOT ADD ANY new Security Group.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
        Rule #4: Review the entire template to ensure it's properly reflecting the actual Security Rules required. Don't add any additional unnecessary rules.
    ''',
    "CloudWatch": '''
        *** IMPORTANT ***
        You must follow all of these rules:
        Rule #0: First analyze the given CloudFormation template. If it doesn't have any CloudWatch,DO NOT ADD ANY new CloudWath.
        Rule #1: There should be absolutely no placeholder values or texts. All values must be valid and ready for deployment
        Rule #2: You must randomize the resource name to avoid conflicts
        Rule #3: You must always respond with the entire CloudFormation template. Not just the fixed code for this specific component
    ''',
}

devops_tasks = '''
    Develop a CloudFormation template to deploy the resources to AWS according to the requirement on the <document> below.
    Lambda function codes are zipped and saved in s3 bucket as given in <packages></packages>
'''

devops_constraints = '''
    You must follow these rules:
    Rule #1: Don't create any resources that are not mentioned in the architecture document
    Rule #2: Never leave any placeholders or test code in your template.
    Rule #3: Entire template must be ready for production release
    Rule #4: Review the template at least 5 times for syntax errors, consistencies, and integration
    Rule #5: You will always rewrite the entire code and return in your response.
    Rule #6: You will give the actual CloudFormation template in ```. 
    Rule #7: There should be only one codeblock of CloudFormation template. No other codeblocks should be presented.

    *** IMPORTANT ***
    Here's an example of a bad response:
    As per the requirement, here's the CloudFormation template
    ```
    AWSTemplateFormatVersion: '2010-09-09'
    Metadata: 
    License: Apache-2.0
    Description: 'AWS CloudFormation Sample Template DynamoDB_Table'
    Parameters:
    HashKeyElementName:
        Description: HashType PrimaryKey Name
        Type: String
        AllowedPattern: '[a-zA-Z0-9]*'
        MinLength: '1'
        MaxLength: '2048'
        ConstraintDescription: must contain only alphanumberic characters
    HashKeyElementType:
        Description: HashType PrimaryKey Type
        Type: String
        Default: S
        AllowedPattern: '[S|N]'
        MinLength: '1'
        MaxLength: '1'
        ConstraintDescription: must be either S or N
    ReadCapacityUnits:
        Description: Provisioned read throughput
        Type: Number
        Default: '5'
        MinValue: '5'
        MaxValue: '10000'
        ConstraintDescription: must be between 5 and 10000
    WriteCapacityUnits:
        Description: Provisioned write throughput
        Type: Number
        Default: '10'
        MinValue: '5'
        MaxValue: '10000'
        ConstraintDescription: must be between 5 and 10000
    Resources:
    myDynamoDBTable:
        Type: AWS::DynamoDB::Table
        Properties:
        AttributeDefinitions:
        - AttributeName: !Ref 'HashKeyElementName'
            AttributeType: !Ref 'HashKeyElementType'
        KeySchema:
        - AttributeName: !Ref 'HashKeyElementName'
            KeyType: HASH
        ProvisionedThroughput:
            ReadCapacityUnits: !Ref 'ReadCapacityUnits'
            WriteCapacityUnits: !Ref 'WriteCapacityUnits'
    Outputs:
    TableName:
        Value: !Ref 'myDynamoDBTable'
        Description: Table name of the newly created DynamoDB table
    ```

    Here's an example of a good response:
    As per the requirement, here's the CloudFormation Template
    ```
    AWSTemplateFormatVersion: '2010-09-09'
    Description: 'CloudFormation Template for DynamoDB Table'

    Resources:
    MyDynamoDBTable:
        Type: 'AWS::DynamoDB::Table'
        Properties:
        TableName: ContentTable
        AttributeDefinitions:
            - AttributeName: ID
              AttributeType: S
            - AttributeName: Date
              AttributeType: S
        KeySchema:
            - AttributeName: ID
              KeyType: HASH
            - AttributeName: Date
              KeyType: RANGE
        ProvisionedThroughput:
            ReadCapacityUnits: 5
            WriteCapacityUnits: 5
        SSESpecification:
            SSEEnabled: true
    ```
'''