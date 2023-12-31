import autogen
import os
import json
import re
from typing import Dict, List
from utils.notetaker import NoteTaker
from utils.seminar import Seminar

from docx import Document

class Design:
    def __init__(self):
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
        
        # combination of all notes from architecture component discussion
        note_collection: str = ''

        # architecture_components = [
        #     {"phase": "high-level summary", "constraints": "Create a summary within 300 words. Do NOT discus any other details."},
        #     {"phase": "file and folder structure", "constraints": "Determine a very detailed file and folder structure. Do NOT discus any other details."},
        #     {"phase": "database requirement and design", "constraints": '''Application will be deployed in {self.cloud} with the following services {self.cloud_services}. Do NOT discus any other details that database schema and requirements.'''},
        #     {"phase": "cloud infrastructure design", "constraints": '''Application will be deployed in {self.cloud} with the following services {self.cloud_services}. Do not talk about CI/CD, networking or basic infrastructure. Do NOT discus any other details.'''}
        # ]

        architecture_components = [
            {"phase": "high-level summary", "constraints": '''You must follow ALL of these rules: 
             Rule #1: Create a summary within 300 words.
             Rule #2: Never any other details.
             Rule #3: Must encapsulate the actual summary in <response></response>.
             ** IMPORTANT **
             Here's an example of a good response:
             Based on the analysis, here's the high-level requirement:
             <response>
             # high level requirement
             </response>

             Here's an example of a bad response:
             <response>
             Based on the analysis, here's the high-level requirement:
             # high level requirement
             </response>
             '''},

            {"phase": "AWS cloud components for this application", "constraints": '''
            ALL of these rules must be followed:
             Rule #1: Only use these services where necessary - API Gateway, Lambda, DynamoDB, S3, SSM, SecurityGroup, IAM, and CloudWatch.
             Rule #2: Never discuss any other details
             Rule #3: Must encapsulate the actual summary in <response></response>.
             Rule #4: There should be no generic descriptions for each of these services.
             Rule #5: Each services must be evaluated against the overall plan and functional requirements to ensure whether they are needed or not.
             Rule #6: There must be naming convention for each of the components
             Rule #7: You must review and adjust the overall recommendation for cohesion.
             Rule #8: This response will be used by another architect to create detailed plan. Keep the integration and cohesion in mind for this round.

            ** Important ** 
            Here's an example of a good response:
             Based on the analysis, here's the high-level requirement
             <response>
            This application will be implemented using the following Cloud Services: API Gateway, Lambda, DynamoDB, S3, SSM, and SecurityGroup.
            API Gateway:
             - API Gateway 1:
                - spec
             - API Gateway 2:
                - spec
            Lambdas:
             - Lambda 1:
                - name:
                - purpose:
             - Lambda 2:
                - name:
                - purpose:
            SSM parameters:
             - Parameter 1:
                - name:
                - purpose:
            DynamoDB:
             - table 1
                - purpose:
                - name:
            </response>
             
            Example of a poor response:
             <response>
            You can use AWS API Gateway, Azure API Gateway for endpoints. You can use Azure Functions, Containers, or AWS to run your application.
            API Gateway
            Lambdas: use lambda for compute
            ssm parameters: use ssm parameters
            DynamoDB: use dynamodb for storing data
            S3 bucket: use s3 bucket to storing files
             </response>

            Now, think step by step on how the given functional requirements should be implemented. Create a cohesive and integrated Cloud Architecture to implement the services. Review your recommendation at least 3 times to ensure integrated plan.
            '''}
        ]

        for component in architecture_components:
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
        

        project_structure_rules = [
            f'''Extract the lambda functions to be created in this format for each Lambda function.
            You must follow this rule:
            Rule #1: You must give each lambda function as separate element encapsulated in <lambda></lambda>

            ** Important **
            Here's an example of bad response
            <lambda>
            lambda 1
            lambda 2
            lambda 3
            </lambda>

            Here's an example of a good response
            Based on the analysis, here's the break-down
            <lambda>
            name:
            description:
            constraints:
            </lambda>
            <lambda>
            name:
            description:
            constraints:
            </lambda>
            
            ''',
            # '''Create OpenAPI spec for AWS API Gateway and provide the response in this format:
            # <apigateway>
            # </apigateway>''',
            # '''Determine if a S3 bucket is required. If it is, then determine S3 bucket name and provide the response in this format:
            # <s3bucket>
            # </s3bucket>'''
        ]
        
        for rule in project_structure_rules:
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
                Revise the project structure based on feedback from user.
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
        seminar_result = self._cto_consultation(product_manager_plan, "NEVER")

        self.architecture_document = seminar_result

        project_structure = self._create_project_structure()
        self.project_structure = project_structure
            
        # if this is not serverless, then project structure is the file structure
        if self.serverless:
            pattern = r"<lambda>.*?name:\s*(\w+).*?</lambda>"
            matches = re.findall(pattern, self.project_structure, re.DOTALL)
            file_paths = [f"/lambda_functions/{name.replace('Handler', '')}/lambda_function.py" for name in matches]
        else:
            file_paths = project_structure.strip().split("\n")[1:-1]

        # initiate source code dict
        for file_path in file_paths:
            self.source_code[file_path] = ""

        print("**** Solution Design Completed ***")