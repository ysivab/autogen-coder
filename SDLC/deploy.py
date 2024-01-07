import autogen
import importlib
import os
import re
import sys

from utils.seminar import Seminar
from utils.deployer import Deployer
from utils.awslambda import deploy_cloudformation, describe_cloudformation

class Deploy:
    def __init__(self, config_type):
        self.config_type = config_type

        # basic information about the project
        self.root_folder: str = None
        self.source_code: dict = {}
        self.architecture_document: str = None
        self.project_name: str = None
        
        # resources to be created to support this application
        self.infra_stack_map: dict = {} # resources to deploy
        self.source_code_uri: dict = [] # packaged and uploaded source code
        self.deployment_template: str = None

        # load common configs
        common_module = importlib.import_module(f"config.{self.config_type}.common")
        self.language = getattr(common_module, 'language', "python")
        self.infra_stack = getattr(common_module, 'infra_stack', ["containers"])
        self.region = getattr(common_module, 'region', 'us-east-1')

        # load custom configs
        config_module = importlib.import_module(f"config.{self.config_type}.deploy")
        self.devops_tasks = getattr(config_module, 'devops_tasks', None)
        self.devops_constraints = getattr(config_module, 'devops_constraints', None)
        self.template_constraints = getattr(config_module, 'template_constraints', None)
        self.resource_constraints = getattr(config_module, 'resource_constraints', None)

        self.tshoot_counter: int = 0 # used to keep the number of times troubleshooting happened

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
    


    def _fix_template(self, task, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Expert to help a develop deployment template. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            {task}
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
            # if there are multiple code blocks, then human involvement required
            if len(matches) == 1:
                source_code = matches[0].strip()
                break

        return source_code


    def _troubleshoot_deployment(self, stack_message):
        if self.tshoot_counter < 10:
            self.deployment_template = self._fix_template(f'''
                Review the following deployment template <template>{self.deployment_template}</template>
                Fix the error as this template is getting the following error message at deployment: {stack_message}
                Packaged source codes are saved in this URI ready for deployment if you need to refer them in your deployment template <packages>{self.source_code_uri}</packages>
                This is the architecture document <document>{self.architecture_document}</document>''', "ALWAYS")
            
            stack = deploy_cloudformation(self.deployment_template, self.region, self.project_name)
            if stack['status']:
                stack_id = stack['stack_id']
                deployment_status = describe_cloudformation(self.region, self.project_name)

                if not deployment_status["status"]:
                    self._troubleshoot_deployment(deployment_status["message"])
            else:
                stack_message = stack['message']
                self.tshoot_counter = self.tshoot_counter + 1
                self._troubleshoot_deployment(stack_message)
        else:
            print("Couldn't troubleshoot template deployment.")
            sys.exit(1)


    def _get_deployment_status(self, stack_id):
        describe_cloudformation(self.region, self.project_name)


    def read_deployment_template(self, template):
        with open(template, 'r', encoding='utf-8') as file:
            self.deployment_template = file.read()


    def deploy_to_sandbox(self):
        if self.deployment_template is None:
            self.deployment_template = self._create_deployment_template("NEVER")

            # review and apply individual resources are properly designed
            # for resource in self.infra_stack_map.keys():
            self.deployment_template = self._fix_template(f'''
                Review the following deployment template <template>{self.deployment_template}</template>
                <constraints>{self.resource_constraints}</constraints>
                Packaged source codes are saved in this URI ready for deployment if you need to refer them in your deployment template <packages>{self.source_code_uri}</packages>
                This is the architecture document <document>{self.architecture_document}</document>''', "ALWAYS")

        if self.config_type == "awslambda":
            # deploy the template and verify stack is successfull "CREATED"
            stack = deploy_cloudformation(self.deployment_template, self.region, self.project_name)
            if stack['status']:
                stack_id = stack['stack_id']
                # self._get_deployment_status(stack_id)
            else:
                stack_message = stack['message']
                # start the troubleshooting cycle
                self._troubleshoot_deployment(stack_message)

            # check the deployment status
            deployment_status = describe_cloudformation(self.region, self.project_name)
            if not deployment_status["status"]:
                self._troubleshoot_deployment(deployment_status["message"])

        # save the deployment template to the project root
        file_path = os.path.join(self.root_folder, 'deployment-template.yml')
        with open(file_path, 'w') as file:
            file.write(self.deployment_template)


       
        # # Work in Progress
        # deployer: Deployer = Deployer()
        # response = deployer.start(user_persona, expert_persona)


