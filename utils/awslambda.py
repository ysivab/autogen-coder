import os
import re
import subprocess
import zipfile
import boto3
import time
import sys

from botocore.exceptions import ClientError
from datetime import datetime

def prepare_lambda_env(language, lambdas) -> []:
    pattern = r"<name>\s*(.*?)\s*</name>"
    func_names = re.findall(pattern, lambdas, re.DOTALL)

    lambda_handler_paths = []

    for func_name in func_names:
        # func_name = re.search(pattern, func, re.DOTALL)
        if language.lower() == "python":
            lambda_handler_paths.append(f'''/lambda_functions/{func_name}/index.py''')
    
    return lambda_handler_paths


def package_lambda(lambda_handler_path, language, root_folder) -> str:
    lambda_dir = os.path.dirname(lambda_handler_path)

    if language.lower() == "python":
        requirements_path = os.path.join(lambda_dir, 'requirements.txt')

        # Temporary directory for dependencies
        package_dir = os.path.join(lambda_dir, 'package')
        # Create the directory
        os.makedirs(package_dir, exist_ok=True)

        # Install dependencies if requirements.txt exists
        if os.path.exists(os.path.join(root_folder, requirements_path)):
            subprocess.run(
                ["pip", "install", "-r", requirements_path, "--target", package_dir],
                cwd=root_folder,
                check=True
            )

        # Create the zip file for the Lambda function
        output_zip = os.path.join(root_folder, lambda_dir, f'{os.path.basename(lambda_dir)}_lambda.zip')
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            package_dir_full_path = os.path.join(root_folder, package_dir)
            if os.path.exists(package_dir_full_path):
                for root, dirs, files in os.walk(package_dir_full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate the archive name to be relative to package_dir
                        archive_name = os.path.relpath(file_path, package_dir_full_path)
                        z.write(file_path, archive_name)


            # Add the lambda function code and any other Python files in the same directory
            for file in os.listdir(os.path.join(root_folder, lambda_dir)):
                if file.endswith('.py'):
                    file_path = os.path.join(root_folder, lambda_dir, file)
                    z.write(file_path, file)

        return output_zip



def upload_lambda(lambda_path, bucket_name) -> str:
    # Create an S3 client
    s3 = boto3.client('s3', region_name='us-east-1')

    # if bucket name is not defined, then assume bucket name to be autogen_coder_{Account_ID}
    if bucket_name == None:
        sts_client = boto3.client('sts')
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity.get('Account')
        bucket_name = f"autogen-coder-{account_id}"

    # create the bucket if it doesn't exist
    try:
        s3.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            pass
        elif e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"Bucket {bucket_name} already exists and is owned by someone else")
            sys.exit(1)
        else:
            print(f"An error occured: {e}")
            sys.exit(1)

    # Extract filename from the file path
    filename = os.path.basename(lambda_path)

    # Generate the file key with the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    key = f"{timestamp}/{filename}"

    # Upload the file
    s3.upload_file(lambda_path, bucket_name, key)

    s3_path = f"s3://{bucket_name}/{key}"

    return s3_path


def deploy_cloudformation(template, region, stack_name) -> {}:
    deployment_result: dict = {
        "status": False
    }

    # Create CloudFormation client
    cf = boto3.client('cloudformation', region_name=region)

    try:
        # Try to create the stack
        response = cf.create_stack(
            StackName=stack_name,
            TemplateBody=template,
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            # OnFailure='DELETE'  # Specify what action to take if stack creation fails
        )
        deployment_result["status"] = True
        deployment_result["stack_id"] = response['StackId']

        return deployment_result
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException':
            print(f"Stack {stack_name} already exists, attempting to update...")
            try:
                # Update the stack
                response = cf.update_stack(
                    StackName=stack_name,
                    TemplateBody=template,
                    Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
                )
                deployment_result["status"] = True
                deployment_result["stack_id"] = response['StackId']

                return deployment_result
            except ClientError as update_error:
                deployment_result["status"] = False
                deployment_result["message"] = update_error
                return deployment_result
        else:
            print(e)
            deployment_result["status"] = False
            deployment_result["message"] = e
            return deployment_result


def describe_cloudformation(region, stack_name) -> {}:
    deployment_status = {
        "status": True, # assume deployment is successful
        "message": [],
        "status_message": None
    }
    # Initialize a CloudFormation client
    cf = boto3.client('cloudformation', region_name=region)

    try:
        # wait until cloud formation template deployment is completed
        while True:
            # Retrieve the stack's current status
            stack = cf.describe_stacks(StackName=stack_name)['Stacks'][0]
            stack_status = stack['StackStatus']
            deployment_status["status_message"] = stack['StackStatus']

            # Check if the stack is still being created or updated
            if stack_status.endswith('IN_PROGRESS'):
                print(f"Stack status is '{stack_status}'. Waiting...")
                time.sleep(10)  # Wait for 10 seconds before checking again
                continue

            # If the stack is no longer in progress, break out of the loop
            print(f"Stack status is '{stack_status}'.")
            break

        # Retrieve and print the stack events
        response = cf.describe_stack_events(StackName=stack_name)
        events = response['StackEvents']

        for event in events:
            event_id = event['EventId']
            status = event['ResourceStatus']
            reason = event.get('ResourceStatusReason', 'No reason provided')
            timestamp = event['Timestamp']
            deployment_status["message"].append({
                "Event_ID": {event_id},
                "Status": {status},
                "Reason": {reason},
                "Timestamp": {timestamp}
            })
            print(f"Event ID: {event_id}, Status: {status}, Reason: {reason}, Timestamp: {timestamp}")

            # Print any error messages
            if 'FAILED' in status or 'ROLLBACK' in status:
                deployment_status["status"] = False
                print(f"Error: {status} - {reason}")
    
    except ClientError as e:
        deployment_status = {
            "status": False, # assume deployment is successful
            "message": []
        }
    
    # if the stack failed, then let's clean it up
    if not deployment_status["status"] and deployment_status["status_message"] == "ROLLBACK_COMPLETE":
        cf.delete_stack(StackName=stack_name)
        print(f"Deletion request sent for stack '{stack_name}'")

        print("Waiting for stack to be deleted ....")
        waiter = cf.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
        print(f"Stack '{stack_name}' has been deleted.")

    return deployment_status

