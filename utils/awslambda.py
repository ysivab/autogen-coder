import os
import re
import subprocess
import zipfile
import boto3
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
            lambda_handler_paths.append(f'''/lambda_functions/{func_name}/lambda_function.py''')
    
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


