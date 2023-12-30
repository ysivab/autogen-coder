import autogen
import os
import json
import re
import subprocess
import shutil

from docx import Document
from utils.notetaker import NoteTaker
from utils.seminar import Seminar
from utils.extract_code import extract_code

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

        self.cloud_stack_map: dict = []

        self.language: str = "Python"
        self.integration_constraints = '''
            - This is for Lambda functions
            - User cannot read text. You must ensure format is in a codeblock with the filename for the dependency
        '''
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )
        self.cloud_services = "API Gateway, Lambda, DynamoDB, S3, SSM, SecurityGroup, IAM, and CloudWatch."


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

    # check for response and summarize
    def _summarizer(self, seminar_notes) -> str:
        source_code: str = None

        notetaker: NoteTaker = NoteTaker()
        summary = notetaker.summarize('''Revise the initial code block from the developer and incorporate feedback from the critic. Remove any duplicate information. Rewrite the code block by including user and critic's feedback. Identify what should be in ```requirements.txt ``` file. Do not give any instruction. You must give only one codeblock, nothing more.''', seminar_notes)

        # pattern = r"(?:\w+)?\s*\n?(.*?)\s*"
        pattern = r"```(?:\w+)?\s*\n(.*?)\n```"
        match = re.search(pattern, summary, re.DOTALL)

        if match:
            source_code = match.group(1).strip()
        else:
            source_code = ""

        return source_code

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
                ** IMPORTANT **
                You must strictly follow all the rules listed below.
                Rule #1
                There should never be any packages that are comes with AWS Lambda

                Rule #2
                You must provide the response in single code block.
                Here's an examples of poorly written response:
                ** poor response**
                text text text
                ```
                import boto3
                ```
                text text text
                ```
                do this next
                ```

                Here's an examples of good response for Python:
                ** good response ***
                ```requirements.txt
                boto3
                ```

                Here's another example of a good response for Node.JS:
                *** good response ***
                ```package.json
                {{
                    "name": "lambda",
                    "version": "1.0.0",
                    "description": "This is a Lambda function",
                    "dependencies": {{
                        "dotenv": "^8.2.0",
                        "express": "^4.17.1"
                    }}
                }}
                '''
        )

        summary = user_proxy.last_message()['content']

        return summary
        

    def _install_dependencies(self, directory, file_path) -> None:
        if self.language.lower() == "python":
            package_directory = os.path.join(directory, "packages")
            file_path = os.path.join(self.root_folder, file_path)

            # if directory already exist, let's clean it
            if os.path.exists(package_directory):
                shutil.rmtree(package_directory)
            os.makedirs(package_directory)

            cmd = [
                "pip",
                "install",
                "-r",
                file_path,
                "--target",
                package_directory
            ]
        

        process = subprocess.run(
            cmd,
            cwd=self.root_folder,
            capture_output=True,
            text=True,
        )

        if process.returncode == 0:
            print(f"Output:\n{process.stdout}")
        else:
            print(f"Error:\n{process.stderr}")


    def _generate_iam_policies(self, source_code, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Here's the full project structure for your reference <project-structure>{self.project_structure}</project-structure>. 
            Write the full code for only this specific component <component>{file_path}</component> only to satisfy requirement on the <document> below.
            You must follow these rules: {self.developer_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            Do NOT write any other classes.
            """
        }

        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
            You must follow all these rules below:
            Rule #1: You will write the code for the specific component you've been asked to develop. Don't write any other components, only focus on your component.
            Rule #2: Your output should be strictly just one code block.
            Rule #3: You will always rewrite the entire code and return in your response.
            Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Software Developer to critique the work",
            "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.
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
        print("IAM Role")


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

                # save processed lambda into cloud stacks
                self.cloud_stack_map.append({"lambda": directory})

                

                