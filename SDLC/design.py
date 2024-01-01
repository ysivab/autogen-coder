import autogen
import os
import re
import importlib

from utils.notetaker import NoteTaker
from utils.seminar import Seminar
# from config.awssls.design import architecture_components, project_structure_rules

class Design:
    def __init__(self, config_type):
        config_module = importlib.import_module(f"config.{config_type}.design")

        self.architecture_components = getattr(config_module, 'architecture_components', None)
        self.project_structure_rules = getattr(config_module, 'project_structure_rules', None)

        self.architecture_document: str = None
        self.root_folder: str = None        
        self.source_code: dict = {}
        self.project_structure: str = ''
        self.notetaker: NoteTaker = NoteTaker()

        # setting variables
        self.language: str = "Python"
        self.serverless: bool = True
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )
    
    # analyzes the high level requirement and detailed requirement to come up with technical guidance
    def _cto_consultation(self, product_manager_plan: str, human_input_mode) -> str:
        # final architecture document
        architecture_document: str = ''

        for component in self.architecture_components:
            phase = component['phase']
            constraints = component['constraints']
            user_persona: dict = {
                "name": "User",
                "description": "This agent only responds once and then never speak again.",
                "system_message": "User. Interact with the Software Architect to discuss the requirement. Final project break-down needs to be approved by this user.",
                "human_input_mode": human_input_mode,
                "task": f"""
                Software Architect, I want you to determine the "{phase}".
                {constraints}
                Product Manager has the following high-level requirement for my application: <plan>{product_manager_plan}</plan>.
                """
            }
            
            critic_persona: dict = {
                "name": "Critic",
                "description": "This agent speaks after Software Architect's response. CTO critique the work done by Software Architect and provides feedback.",
                "system_message": f'''Critic. You will review SoftwareArchitect's response and compare it with user's request. Only review {phase} and nothing more.
                Ensure you follow this rule: {constraints}
                Programming language to be used: {self.language}.
                Provide feedback to the Software Architect to revise the plan 
                '''
            }

            expert_persona: dict = {
                "name": "SoftwareArchitect",
                "description": "This agent is the the first speaker and the last speaker in this seminar",
                "system_message": f'''Software Architect. You are an expert in Cloud, microservices and Python development. 
                You analyze functional requirements thoroughly and break-down how this can be implemented in {self.language}.
                You'll be determining {phase}
                You must follow this rule: {constraints}
                Revise your entire plan based on feedback from Chief Technology Officer and User until user approval.
                '''
            }

            seminar: Seminar = Seminar()
            seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

            # find the last code block and send it as the source code
            # architecture_document: str = None
            for message in reversed(seminar_notes):
                pattern = r"<response>(?:\w+)?\s*\n(.*?)\n</response>"
                matches = re.findall(pattern, message['content'], re.DOTALL)
                
                # only one response is expected. if there's no <response> OR
                # if there are multiple <response>, then human involvement required
                if len(matches) == 1:
                    architecture_document = architecture_document + "\n" + matches[0].strip()
                    break

        # write to disk
        file_path = os.path.join(self.root_folder, 'architecture-design.md')
        with open(file_path, 'w') as file:
            file.write(architecture_document)
        
        return architecture_document

    # extract a project plan
    # project plan should be specific instructions to the developers to execute
    # it should be split by files, and other common instructions
    def _create_project_structure(self) -> str:
        project_structure: str = ''

        # project_structure_rules = [
        #     '''Extract full file paths (in this format 
        #     <files>
        #     full path
        #     </files>)'''
        # ]
        

        # project_structure_rules = [
        #     f'''Extract the lambda functions to be created in this format for each Lambda function.
        #     You must follow this rule:
        #     Rule #1: You must give each lambda function as separate element encapsulated in <lambda></lambda>

        #     ** Important **
        #     Here's an example of bad response
        #     <lambda>
        #     lambda 1
        #     lambda 2
        #     lambda 3
        #     </lambda>

        #     Here's an example of a good response
        #     Based on the analysis, here's the break-down
        #     <lambda>
        #     name:
        #     description:
        #     constraints:
        #     </lambda>
        #     <lambda>
        #     name:
        #     description:
        #     constraints:
        #     </lambda>
            
        #     ''',
            # '''Create OpenAPI spec for AWS API Gateway and provide the response in this format:
            # <apigateway>
            # </apigateway>''',
            # '''Determine if a S3 bucket is required. If it is, then determine S3 bucket name and provide the response in this format:
            # <s3bucket>
            # </s3bucket>'''
        # ]
        
        for rule in self.project_structure_rules:
            user_proxy = autogen.UserProxyAgent(
                name = "User",
                llm_config={
                    # "temperature": 0,
                    "config_list": self.config_list,
                },
                system_message = "User. Interact with the Software Developer to create project structure based on the architecture diagram. Final project break-down needs to be approved by this user.",
                code_execution_config=False,
            )

            software_developer = autogen.AssistantAgent(
                name = "SoftwareDeveloper",
                llm_config={
                    # "temperature": 0,
                    "config_list": self.config_list,
                },
                system_message = f'''Software Developer. You are an expert Software Developer specializing in Python.
                You will review the architecture document and {rule}
                Revise the project structure based on feedback from user and critic.
                '''
            )

            groupchat = autogen.GroupChat(agents=[user_proxy, software_developer], messages=[], max_round=3)
            manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                    # "temperature": 0,
                    "config_list": self.config_list,
                },)

            user_proxy.initiate_chat(
                manager,
                message=f"""{rule} for this project from this architecture document: <document>{self.architecture_document}</document>
                """
            )

            for message in reversed(groupchat.messages):
                if message['name'] == 'SoftwareDeveloper' and message['content'] is not None:
                    project_structure = project_structure + '\n' + message['content']
                    break
        
        return project_structure
            

    def architect_solution(self, product_manager_plan: str) -> None:
        seminar_result = self._cto_consultation(product_manager_plan, "ALWAYS")

        self.architecture_document = seminar_result

        project_structure = self._create_project_structure()
        self.project_structure = project_structure
        pattern = r"<response>.*?name:\s*(\w+).*?</response>"
        matches = re.findall(pattern, self.project_structure, re.DOTALL)

        # if this is not serverless, then project structure is the file structure
        if self.serverless:
            file_paths = [f"/lambda_functions/{name.replace('Handler', '')}/lambda_function.py" for name in matches]
        else:
            file_paths = [{name} for name in matches]
            # file_paths = project_structure.strip().split("\n")[1:-1]

        # initiate source code dict
        for file_path in file_paths:
            self.source_code[file_path] = ""
