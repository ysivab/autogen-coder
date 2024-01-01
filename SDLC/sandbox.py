import autogen
import os
import json
import re
import subprocess
import shutil

from utils.seminar import Seminar
from utils.deployer import Deployer

class Sandbox:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}
        self.project_structure: str = None
        self.architecture_document: str = None

        self.serverless: bool = True

        self.cloud_stack_map: dict = []
        self.source_code_on_disk: dict = []
        self.allowed_cloud_resources = ["AWS-API-Gateway", "Lambda", "S3-bucket", "DynamoDB", "SSM", "IAM", "SecurityGroup", "CloudWatch"]
        self.cloud_resource_constraints = {
            "AWS-API-Gateway": '''
             *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"Lambda": '''
Each Lambda function code and all dependent libraries are in these folder {json.dumps(self.cloud_stack_map)}
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You need to zip and upload the Lambda code to s3://olnyth/ and use the uploaded zip to deploy Lambda
Rule #4: You must randomize the resource name to avoid conflicts
''',
"S3-bucket": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"DynamoDB": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"SSM": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"IAM": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"SecurityGroup": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
"CloudWatch": '''
 *** IMPORTANT ***
You must follow all of these rules:
Rule #0: Never tell me to modify or replace any value. Do it yourself and give a command that's executable.
Rule #1: Deploy resource using AWS CLI in ca-central-1 region
Rule #2: use the account ID "320499649792"
Rule #3: You must randomize the resource name to avoid conflicts
''',
        }

        self.language: str = "Python"

        self.sandbox_constraints = '''
        *** IMPORTANT ***
You must follow all of these rules:
Rule #1: First read the entire architecture document and create a high-level plan
Rule #2: Create the resources using AWS CLI in ca-central-1 region.
Rule #3: Use this S3 bucket "olnyth" for storing any depoyment assets.
            Rule #4: randomize name of the resource to avoid any overlaps
            Rule #5: Use the account ID "320499649792"
            Rule #6: If this is Lambda, you must first zip and upload the Lambda to s3://olnyth/
'''
        self.devops_constraints = '''
            You must follow these rules:
            Rule #1: Don't create any resources that are not mentioned in the architecture document
            Rule #2: Never leave any placeholders or test code in your template.
            Rule #3: Entire template must be ready for production release
            Rule #4: Review the template at least 5 times for syntax errors, consistencies, and integration
        '''

        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )


    # def _generate_iam_policies(self, source_code, human_input_mode) -> str:
    #     user_persona: dict = {
    #         "name": "User",
    #         "description": "This agent only responds once and then never speak again.",
    #         "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
    #         "human_input_mode": human_input_mode,
    #         "task": f"""
    #         Here's the full project structure for your reference <project-structure>{self.project_structure}</project-structure>. 
    #         Write the full code for only this specific component <component>{file_path}</component> only to satisfy requirement on the <document> below.
    #         You must follow these rules: {self.developer_constraints}
    #         This is the architecture document <document>{self.architecture_document}</document>
    #         Do NOT write any other classes.
    #         """
    #     }

    #     expert_persona: dict = {
    #         "name": "CloudEngineer",
    #         "description": "This agent will be the first speaker and the last speaker in this seminar",
    #         "system_message": f'''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
    #         You must follow all these rules below:
    #         Rule #1: You will write the code for the specific component you've been asked to develop. Don't write any other components, only focus on your component.
    #         Rule #2: Your output should be strictly just one code block.
    #         Rule #3: You will always rewrite the entire code and return in your response.
    #         Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
    #         '''
    #     }

    #     critic_persona: dict = {
    #         "name": "Critic",
    #         "description": "This agent only speaks once, and only after Cloud Engineer to critique the work",
    #         "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.
    #         You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.''',
    #     }

    #     seminar: Seminar = Seminar()
    #     seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

    #     # find the last code block and send it as the source code
    #     source_code: str = None
    #     for message in reversed(seminar_notes):
    #         pattern = r"```(?:\w+)?\s*\n(.*?)\n```"
    #         matches = re.findall(pattern, message['content'], re.DOTALL)
            
    #         # only one code block is expected. if there's no code block OR
    #         # if there are multiple code blocks, then human involve required
    #         if len(matches) == 1:
    #             source_code = matches[0].strip()
    #             break      
    #     print("IAM Role")
            
    
    def _sandbox_application(self, human_input_mode, resource, details) -> None:
        user_persona: dict = {
            "name": "User",
            "human_input_mode": human_input_mode,
            "task": f"""
            Create the following resource "{resource}" to support the application. More details of this resource according to the application usage: {details}
            {self.cloud_resource_constraints[resource]}
            """
        }

        expert_persona: dict = {
            "name": "DevOpsEngineer",
        }

        deployer: Deployer = Deployer()
        results = deployer.start(user_persona, expert_persona)


    def _create_cloudformation(self, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the DevOps Engineer to help a develop deployment template. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Develop a CloudFormation template to deploy the resources to AWS according to the requirement on the <document> below.
            Lambda function codes are zipped and saved in s3 bucket with the lambda function name as key s3://am-autogen-coder/{{key}}
            {self.devops_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            Do NOT write any other classes.
            """
        }

        expert_persona: dict = {
            "name": "DevOpsEngineer",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You analyze full architecture document thoroughly.
            You must follow all these rules below:
            Rule #1: You will focus only on the components mentioned on the architecture document. Nothing more.
            Rule #2: Your output should be strictly just one code block.
            Rule #3: You will always rewrite the entire code and return in your response.
            Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after DevOpsEngineer to critique the work",
            "system_message": '''Critic. Double check plan, and code from other agents and provide feedback. DevOps Engineer must return the output in just one code block.
            You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # find the last code block and send it as the source code
        source_code: str = None
        for message in reversed(seminar_notes):
            pattern = r"```(?:\w+)?\s*\n(.*?)\n```"
            matches = re.findall(pattern, message['content'], re.DOTALL)
            
            # only one code block is expected. if there's no code block OR
            # if there are multiple code blocks, then human involve required
            if len(matches) == 1:
                source_code = matches[0].strip()
                break

        print("CloudFormation Created")
        return source_code
    
                
    def deploy_to_sandbox(self):
        if self.serverless is True:
            for resource, details in self.cloud_stack_map.items():
                self._sandbox_application("NEVER", resource, details)
            # cloud_formation_template = self._create_cloudformation("NEVER")

            # print(cloud_formation_template)
                