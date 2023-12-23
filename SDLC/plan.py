import autogen
import os
import json
import sys
import re

from docx import Document

class Plan:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.cpo_plan: dict = None
        self.cto_plan: str = None
        self.product_manager_plan: dict = []

    
    # check if document is valid and not empty
    # extract content and save it in requirements
    def read_requirements(self, doc_path) -> None:
        doc = Document(doc_path)
        self.requirements = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        print(self.requirements)

    
    # for each functional requirement, gather more details if required from the user
    def _gather_requirements(self, component_name: str, component_details: str) -> dict:
        config_list=[
            {
                "model": "gpt-3.5-turbo-16k",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]
    
        _user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config = config_list,
            system_message = '''User. Interact with Product Manager to discuss the requirement. You are the final decision maker for the features''',
            code_execution_config = False
        )

        _product_manager = autogen.AssistantAgent(
            name = "ProductManager",
            llm_config = config_list,
            system_message = '''Product Manager. You are an expert in Product Development. You analyze business requirements thoroughly and create a comprehensive product functional requirement. Functional requirement must include schema details for database, and other details. Check your final product requirement with the User.
            If the user provides any feedback, review the feedback with the business requirement thoroughly and recreate the comprehensive product functional requirement.
            Provide the very detailed functional requirement in this format in only one code block ```{"ComponentName": "", "FunctionalRequirement": ""}```'''
        )

        _critic = autogen.AssistantAgent(
            name="Critic",
            llm_config=config_list,
            system_message="Critic. Double check product requirement from the document, Product Manager and provide feedback to Product Manager.Ensure FunctionalRequirement includes schema, and full comprehensive details to support the functionality. You must make sure there are no placeholders. You must ensure response is always encapsulated in ```json{}``` format.",
            # llm_config=gpt4_config,
        )

        _groupchat = autogen.GroupChat(agents=[_user_proxy, _product_manager, _critic], messages=[], max_round=10)
        _manager = autogen.GroupChatManager(groupchat=_groupchat, llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },)

        _user_proxy.initiate_chat(
            _manager,
            message="This is my business requirement. Please write me a comprehensive product functional requirement for the component: " + component_name + " which implements: " + component_details + ". The full requirement document for your reference: " + self.requirements,
        )

        product_manager_message = None
        for message in reversed(_groupchat.messages):
            if message['name'] == 'ProductManager' and message['content'] is not None:
                product_manager_message = message['content']
                break
        
        product_manager_plan = None
        if product_manager_message != "":
            regex = r"```(?:json)?\s*\n?({.*?})\s*\n?```"
            matches = re.finditer(regex, product_manager_message, re.DOTALL)
            for match in matches:
                code = match.group(1).strip()
                print(code)
                if "CODE" in code:
                    continue
                product_manager_plan = json.loads(code)
    
        return product_manager_plan


    def _consult_with_cto(self) -> None:
        config_list=[
            {
                "model": "gpt-3.5-turbo-16k",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config = config_list,
            system_message = "User. Interact with agents to discuss the requirement. Final project break-down needs to be approved by this user.",
            code_execution_config = False
        )

        cto = autogen.AssistantAgent(
            name = "ChiefTechnologyOfficer",
            llm_config = config_list,
            system_message = '''Chief Technology Officer. You are an expert in microservice design, software development and cloud architecture. You analyze functional requirements thoroughly and decide the high-level architecture.
            Decide which programming language this should be built in and provide this info in <language> tag.
            Decide project structure including folders and files for this application and send it in <filestructure> tag.
            Don't send any other tags other than <language> and <filestructure>.
            '''
        )

        critic = autogen.AssistantAgent(
            name="Critic",
            llm_config=config_list,
            system_message='''Critic. Double check plan, claims, code from other agents and provide feedback. Check and ensure response is given in <language> and <filestructure> tags. There should be only one of each. You must make sure there are no placeholders.''',
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, cpo, critic], messages=[], max_round=10)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },)

        user_proxy.initiate_chat(
            manager,
            message="This is my functional requirement. Please write me a comprehensive product functional requirement for a technical implementaiton: " + self.requirements,
        )


    # Review the word document and create high-level components
    def analyze_and_plan(self) -> None:
        config_list=[
            {
                "model": "gpt-3.5-turbo-16k",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config=config_list,
            system_message = "User. Interact with the Chief Product Officer to discuss the requirement. Final project break-down needs to be approved by this user.",
            code_execution_config=False,
        )

        cpo = autogen.AssistantAgent(
            name = "ChiefProductOfficer",
            llm_config=config_list,
            system_message = '''Chief Product Officer. You are an expert in complex product development. You analyze business requirements thoroughly and decide how this large complex product should be split into individual components.
            If the user provides any feedback, review the feedback with the business requirement thoroughly and recreate the component break-down.
            Provide all components break-down in this format in one code block: ```[{"ComponentName": "", "ComponentDetails": ""]```}
        '''
        )

        critic = autogen.AssistantAgent(
            name="Critic",
            llm_config=config_list,
            system_message='''Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan follows this structure: ```[{"ComponentName": "", "ComponentDetails": ""}]``` for each service breakdown. There should be only one code block. You must make sure there are no placeholders.''',
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, cpo, critic], messages=[], max_round=10)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },)

        user_proxy.initiate_chat(
            manager,
            message="This is my business requirement. Please write me a comprehensive product functional requirement for a technical implementaiton: " + self.requirements,
        )

        cpo_message = None
        for message in reversed(groupchat.messages):
            if message['name'] == 'ChiefProductOfficer' and message['content'] is not None:
                cpo_message = message['content']
                break

        if cpo_message != "":
            regex = r"(.+?)\n```.*?\n(.*?)```"
            matches = re.finditer(regex, cpo_message, re.DOTALL)
            for match in matches:
                code = match.group(2)
                if "CODE" in code:
                    continue
                self.cpo_plan = json.loads(code)

        for component in self.cpo_plan:
            component_name = component.get("ComponentName", "")
            component_details = component.get("ComponentDetails", "")
            product_features = self._gather_requirements(component_name, component_details)
            
            if isinstance(product_features, dict):
                self.product_manager_plan.append(product_features)
            else:
                print("Product Feature format is incorrect: " + product_features)
        
        

        print("**** Completed with analysis and planning phase ****")