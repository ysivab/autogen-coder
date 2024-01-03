import autogen
import os
import importlib
import re
import subprocess
import shutil

from utils.seminar import Seminar
from utils.awslambda import package_lambda, upload_lambda

class Integrate:
    def __init__(self, config_type):
        self.config_type = config_type

        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}
        self.project_structure: str = None
        self.architecture_document: str = None

        # load common configs
        common_module = importlib.import_module(f"config.{self.config_type}.common")
        self.language = getattr(common_module, 'language', "python")
        self.infra_stack = getattr(common_module, 'infra_stack', ["containers"])

        # load custom configs
        config_module = importlib.import_module(f"config.{self.config_type}.integrate")
        self.devops_constraints = getattr(config_module, 'devops_constraints', None)
        self.rules_identify_dependencies = getattr(config_module, 'rules_identify_dependencies', None)
        self.rules_identify_resources = getattr(config_module, 'rules_identify_resources', None)

        self.cloud_stack_map: dict = {}

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
                {self.rules_identify_dependencies}
                '''
        )

        summary = user_proxy.last_message()['content']

        return summary
        

    def _install_dependencies(self, directory, file_path) -> None:
        if self.config_type.lower() == "awslambda":
            packaged_lambda = package_lambda(file_path, self.language, self.root_folder)
            lambda_code = upload_lambda(packaged_lambda, self.asset_bucket)
            print("23942830498290348203948290348290384209384234")
            print(lambda_code)
            print("23942830498290348203948290348290384209384234")
        else:
            cmd = []
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

        
    def _identify_resource(self, resource, human_input_mode) -> None:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the DevOps Engineer to help a develop deployment plan. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Identify if {resource} is required to support the application according to the requirement on the <document> below.
            {self.devops_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            {self.rules_identify_resources}
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


    def resolve_dependency(self):
        if self.config_type == "awslambda":
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

                # self._upload_code_to_s3(directory)

                # save processed lambda into cloud stacks
                # self.source_code_on_disk.append({"lambda": "path - " + os.path.join(self.root_folder, directory)})


    def map_resources(self):
        for resource in self.infra_stack:
            self._identify_resource(resource, "NEVER")

