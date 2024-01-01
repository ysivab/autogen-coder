import autogen
import os
import json
import re
import subprocess
import shutil

from utils.seminar import Seminar
from utils.deployer import Deployer

from config.awssls.integrate import devops_constraints, rules_identify_dependencies, rules_identify_resources
from config.awssls.common import language, allowed_cloud_resources

class Integrate:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}
        self.project_structure: str = None
        self.architecture_document: str = None

        self.serverless: bool = True

        self.cloud_stack_map: dict = {}
        self.source_code_on_disk: dict = []

        self.asset_bucket: str = "olnyth"

        
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )


    # software developer to write code to the disk
    def _write_code_to_disk(self, file_path, code):
        # Extract directory path and file name
        file_path = os.path.join(self.root_folder, file_path.lstrip('/'))
        directory = os.path.dirname(file_path)

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

         # Check if the file exists; if so, delete it
        if os.path.isfile(file_path):
            os.remove(file_path)

        # Write content to the file
        with open(file_path, 'w') as file:
            file.write(code)


    def _identify_and_add_dependencies(self, source_code, human_input_mode) -> None:
        expert = autogen.AssistantAgent(
            name = "Expert",
            llm_config={
                "temperature": 0,
                "config_list": self.config_list,
            }
        )

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config={
                "config_list": self.config_list,
            },
            human_input_mode = human_input_mode,
            max_consecutive_auto_reply = 0,
            code_execution_config=False,
        )

        user_proxy.initiate_chat(
            expert,
            message=f'''
                Identify the dependencies for the source code below.
                Source code: <code>{source_code}</code>
                {rules_identify_dependencies}
                '''
        )

        summary = user_proxy.last_message()['content']

        return summary
        

    def _install_dependencies(self, directory, file_path) -> None:
        if language.lower() == "python":
            package_directory = os.path.join(directory, "packages")
            file_path = os.path.join(self.root_folder, file_path)
            lambda_path = os.path.join(self.root_folder, directory)
            lambda_zip_path = os.path.join(lambda_path, directory.replace('lambda_functions/', '') + ".zip")

            # if directory already exist, let's clean it
            if os.path.exists(self.root_folder + "/" + package_directory):
                shutil.rmtree(self.root_folder + "/" + package_directory)
            os.makedirs(self.root_folder + "/" + package_directory)


            print("lambda_path: " + lambda_path)
            print("lambda_zip_path: " + lambda_zip_path)
            print("file_path: " + file_path)
            print("package_directory: " + package_directory)

            cmd = [
                [
                    "pip",
                    "install",
                    "-r",
                    file_path,
                    "--target",
                    package_directory
                ],
                [
                    "zip",
                    "-r",
                    lambda_zip_path,
                    package_directory
                ],
                [
                    "zip",
                    "-u",
                    lambda_zip_path,
                    directory + "/lambda_function.py"
                ]
            ]
        
        for command in cmd:
            process = subprocess.run(
                command,
                cwd=self.root_folder,
                capture_output=True,
                text=True,
            )

            if process.returncode == 0:
                print(f"Output:\n{process.stdout}")
            else:
                print(process.stdout)
                print(f"Error:\n{process.stderr}")



    # def _create_cloudformation(self, human_input_mode) -> str:
    #     user_persona: dict = {
    #         "name": "User",
    #         "description": "This agent only responds once and then never speak again.",
    #         "system_message": "User. Interact with the DevOps Engineer to help a develop deployment template. Final project break-down needs to be approved by this user.",
    #         "human_input_mode": human_input_mode,
    #         "task": f"""
    #         Develop a CloudFormation template to deploy the resources to AWS according to the requirement on the <document> below.
    #         Lambda function codes are zipped and saved in s3 bucket with the lambda function name as key s3://am-autogen-coder/{{key}}
    #         {self.devops_constraints}
    #         This is the architecture document <document>{self.architecture_document}</document>
    #         Do NOT write any other classes.
    #         """
    #     }

    #     expert_persona: dict = {
    #         "name": "DevOpsEngineer",
    #         "description": "This agent will be the first speaker and the last speaker in this seminar",
    #         "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You analyze full architecture document thoroughly.
    #         You must follow all these rules below:
    #         Rule #1: You will focus only on the components mentioned on the architecture document. Nothing more.
    #         Rule #2: Your output should be strictly just one code block.
    #         Rule #3: You will always rewrite the entire code and return in your response.
    #         Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
    #         '''
    #     }

    #     critic_persona: dict = {
    #         "name": "Critic",
    #         "description": "This agent only speaks once, and only after DevOpsEngineer to critique the work",
    #         "system_message": '''Critic. Double check plan, and code from other agents and provide feedback. DevOps Engineer must return the output in just one code block.
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

    #     print("CloudFormation Created")
    #     return source_code
        
    def _identify_resource(self, resource, human_input_mode) -> None:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the DevOps Engineer to help a develop deployment plan. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Identify if {resource} is required to support the application according to the requirement on the <document> below.
            {devops_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            {rules_identify_resources}
            """
        }

        expert_persona: dict = {
            "name": "DevOpsEngineer",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You analyze full architecture document thoroughly.
            You must follow all these rules below:
            Rule #1: You will focus only on this component {resource} on the architecture document. Nothing more.
            Rule #2: Only components details you identify must be encapsulated in <response></response>
            Rule #3: In each response, you will keep repeating the entire details of only the component in <response></response>
            Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after DevOpsEngineer to critique the work",
            "system_message": '''Critic. Double check plan, and break-down from other agents and provide feedback. DevOps Engineer must return the output component details in <response></response> tag
            You must follow one rule: Always list all details of the component in <response></response> in your response. Not just the suggestion.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # find the last code block and send it as the source code
        # source_code: str = None
        for message in reversed(seminar_notes):
            pattern = r"<response>(?:\w+)?\s*\n(.*?)\n</response>"
            match = re.search(pattern, message['content'], re.DOTALL)
            
            if match:
                self.cloud_stack_map[resource] = match.group(1).strip()
                break
            # only one code block is expected. if there's no code block OR
            # if there are multiple code blocks, then human involve required
            # for match in matches:
            #     self.cloud_stack_map.append({"resource": match.strip()})

        # print(json.dumps(self.cloud_stack_map))
        # return source_code


    def _upload_code_to_s3(self, directory) -> None:
        if language.lower() == "python":
            lambda_directory = os.path.join(self.root_folder, directory)
            lambda_zip_path = os.path.join(lambda_directory, directory.replace('lambda_functions/', '') + ".zip")

            files: str = ''
            # get all the files in the lambda directory for packaging
            for file in os.listdir(lambda_directory):
                # Create full path
                full_path = os.path.join(directory, file)

                # Check if it's a file and not a directory
                if os.path.isfile(full_path):
                    files = files + full_path + ' '
                # print("full_path: " + full_path)
            # files = ' '.join(files)
            print("files joined: " + files)
            cmd = [
                [
                    "zip",
                    "-u",
                    lambda_zip_path,
                    files
                ],
                [
                    "aws",
                    "s3",
                    "cp",
                    lambda_zip_path,
                    "s3://" + self.asset_bucket + "/" + directory + ".zip"
                ]
            ]
        
        for command in cmd:
            process = subprocess.run(
                command,
                cwd=self.root_folder,
                capture_output=True,
                text=True,
            )

            if process.returncode == 0:
                print(f"Output:\n{process.stdout}")
            else:
                print(f"Error:\n{process.stderr}")
        # user_persona: dict = {
        #     "name": "User",
        #     "description": "This is the user that coordinates the entire flow.",
        #     # "description": "This agent only responds once and then never speak again.",
        #     "system_message": "User. Interact with the DevOps Engineer to help deploy resources to cloud. Final project break-down needs to be approved by this user.",
        #     "human_input_mode": human_input_mode,
        #     "task": f"""
        #     Lambda code, and dependency packages are in this directory {os.path.join(self.root_folder, directory)}. This is a {self.language} Lambda. Upload this code to this s3 bucket - s3://olnyth/.
        #     """
        # }

        # expert_persona: dict = {
        #     "name": "DevOpsEngineer",
        #     "description": "This role reviews the requirement from the user and make the first response. This agent also listens to the feedback from Critic and make the necessary adjustment",
        #     # "description": "This agent will be the first speaker and the last speaker in this seminar",
        #     "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You analyze full architecture document thoroughly.
        #     You must follow all these rules below:
        #     Rule #1: Never ask the user to modify or replace any value. Do it yourself and give a command that's executable.
        #     Rule #3: Use the account ID "320499649792"
        #     '''
        # }

        # # critic_persona: dict = {
        # #     "name": "Critic",
        # #     "description": "This agent will review the recommendation from DevOpsEngineer and provide feedback to DevOpsEngineer",
        # #     # "description": "This agent only speaks once, and only after DevOpsEngineer to critique the work",
        # #     "system_message": '''Critic. Double check plan, and code from other agents and provide feedback. DevOps Engineer must return the output in just one code block.
        # #     You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.''',
        # # }

        # deployer: Deployer = Deployer()
        # results = deployer.start(user_persona, expert_persona)


    def resolve_dependency(self):
        if self.serverless is True:
            # group files by directory
            directory_files = {}
            for path, content in self.source_code.items():
                directory, file_name = path.rsplit('/', 1)
                directory_name = directory.split('/')[-1]
                directory_files[directory_name] = {}
                directory_files[directory_name][file_name] = content

            # iterate over each directory and process its files
            for directory, files in directory_files.items():
                directory = os.path.join("lambda_functions", directory)
                # installation_path = os.path.join(self.root_folder, directory.lstrip('/'))
                source_code = ', '.join(f"{fname}: ```{content}```" for fname, content in files.items())
                
                dependencies = self._identify_and_add_dependencies(source_code, "NEVER")

                pattern = r'```(.*?)\n(.*?)\s+```'
                matches = re.findall(pattern, dependencies, re.DOTALL)

                # if there's more than one or no dependency file, then let's get the human involved to confirm
                if len(matches) != 1:
                    dependencies = self._identify_and_add_dependencies(source_code, "ALWAYS")
                else:
                    for file_name, content in matches:
                        packages = '\n'.join(content.strip().splitlines())
                        file_path = os.path.join(directory, file_name)
                        self._write_code_to_disk(file_path, packages)

                self._install_dependencies(directory, file_path)

                self._upload_code_to_s3(directory)

                # save processed lambda into cloud stacks
                self.source_code_on_disk.append({"lambda": "path - " + os.path.join(self.root_folder, directory)})


    def map_resources(self):
        for allowed_resource in allowed_cloud_resources:
            self._identify_resource(allowed_resource, "NEVER")

