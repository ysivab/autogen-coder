import autogen
import importlib
import os
import re
import subprocess

from utils.seminar import Seminar
from utils.deployer import Deployer

class Deploy:
    def __init__(self, config_type):
        self.config_type = config_type

        # basic information about the project
        self.root_folder: str = None
        self.source_code: dict = {}
        self.architecture_document: str = None
        
        # resources to be created to support this application
        self.infra_stack_map: dict = {} # resources to deploy
        self.source_code_uri: dict = [] # packaged and uploaded source code
        self.deployment_template: str = None

        # load common configs
        common_module = importlib.import_module(f"config.{self.config_type}.common")
        self.language = getattr(common_module, 'language', "python")
        self.infra_stack = getattr(common_module, 'infra_stack', ["containers"])

        # load custom configs
        config_module = importlib.import_module(f"config.{self.config_type}.deploy")
        self.devops_tasks = getattr(config_module, 'devops_tasks', None)
        self.devops_constraints = getattr(config_module, 'devops_constraints', None)
        self.template_constraints = getattr(config_module, 'template_constraints', None)
        self.resource_constraints = getattr(config_module, 'resource_constraints', None)

        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )


    def _create_deployment_template(self, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Expert to help a develop deployment template. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            {self.devops_tasks}
            <packages>{self.source_code_uri}</packages>
            {self.devops_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            """
        }

        expert_persona: dict = {
            "name": "Expert",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You will analyze the architecture document and create a deployment template as per user's request.
            {self.template_constraints}
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Expert to critique the work",
            "system_message": f'''Critic. Double check plan, and code from other agents and provide feedback. DevOps Engineer must return the output in just one code block.
            You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.
            {self.template_constraints}
            '''
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

        return source_code
    


    def _apply_resource_constraints(self, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Expert to help a develop deployment template. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Review the following deployment template <template>{self.deployment_template}</template>
            <constraints>{self.resource_constraints}</constraints>
            Packaged source codes are saved in this URI ready for deployment if you need to refer them in your deployment template <packages>{self.source_code_uri}</packages>
            This is the architecture document <document>{self.architecture_document}</document>
            Source code for your reference: <source_code>{self.source_code}</source_code>
            """
        }

        expert_persona: dict = {
            "name": "Expert",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''DevOps Engineer. You are an expert DevOps Engineer. You will analyze the architecture document and create a deployment template as per user's request.
            These are the resource constraints for your reference <constraints>{self.resource_constraints}</constraints>
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Expert to critique the work",
            "system_message": f'''Critic. Double check plan, and code from other agents and provide feedback. DevOps Engineer must return the output in just one code block.
            You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.
            These are the resource constraints for your reference <constraints>{self.resource_constraints}</constraints>
            '''
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

        return source_code



    def deploy_to_sandbox(self):
        self.deployment_template = self._create_deployment_template("ALWAYS")

        # review and apply individual resources are properly designed
        # for resource in self.infra_stack_map.keys():
        self.deployment_template = self._apply_resource_constraints("NEVER")

        # save the deployment template to the project root
        file_path = os.path.join(self.root_folder, 'deployment-template.yml')
        with open(file_path, 'w') as file:
            file.write(self.deployment_template)


        # deploy the application
        user_persona: dict = {
            "name": "User",
            "human_input_mode": "NEVER",
            "task": f"""
            Deployment file is created and saved under {file_path}. The content of the template file is as follows for your reference only <file>{self.deployment_template}</file>.
            All necessary access keys are already uploaded to the enviornment variable. Deploy this template file to the platform. 
            *** IMPORTANT ***
            Do not give me text instructions. Write me a bash / shell script to run. I'll return back with the results. Always give me shell / bash commands, and never text instructions.
            """
        }

        expert_persona: dict = {
            "name": "DevOpsEngineer",
        }

        # Work in Progress
        # deployer: Deployer = Deployer()
        # response = deployer.start(user_persona, expert_persona)


