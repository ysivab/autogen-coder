import autogen
import os
import json
import re

from docx import Document

class Design:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.cto_plan: dict = []
        self.pm_plan: dict = []
    
    
    # analyzes the high level requirement and detailed requirement to come up with technical guidance
    def cto_consultation(self, cpo_plan: dict, product_manager_plan: dict) -> None:
        cpo_plan = json.dumps(cpo_plan)
        product_manager_plan = json.dumps(product_manager_plan)

        config_list=[
            {
                "model": "gpt-3.5-turbo-16k",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },
            system_message = "User. Interact with the CTO to discuss the requirement. Final project break-down needs to be approved by this user.",
            code_execution_config=False,
        )

        # engineer = autogen.AssistantAgent(
        #     name = "ChiefTechnologyOfficer",
        #     llm_config={
        #         "timeout": 600,
        #         "cache_seed": 42,
        #         "model": "gpt-3.5-turbo",
        #         "config_list": config_list,
        #     },
        #     system_message = '''ChiefTechnologyOfficer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
        # Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
        # If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
        # '''
        # )
        cto = autogen.AssistantAgent(
            name = "ChiefTechnologyOfficer",
            llm_config = config_list,
            system_message = '''Chief Technology Officer. You are an expert in microservice design, software development and cloud architecture. You analyze functional requirements thoroughly and decide the high-level architecture.
            You like to write this application in Python.
            Decide project structure including folders and files for this application.
            Write only the skeleton project structure in this format ```json[{"ComponentName": 'common or ComponentName from product manager's plan', "filePath": ['full-file-path-1.py', 'full-file-path-2.py'], "content": "...."}]```
            '''
        )

        # executor = autogen.UserProxyAgent(
        #     name="Executor",
        #     llm_config={
        #         "timeout": 600,
        #         "model": "gpt-3.5-turbo",
        #         "cache_seed": 42,
        #         "config_list": config_list,
        #     },
        #     system_message="Executor. Execute the code written by the engineer and report the result.",
        #     human_input_mode="NEVER",
        #     code_execution_config={"last_n_messages": 3, "work_dir": "coding"},
        # )

        critic = autogen.AssistantAgent(
            name="Critic",
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },
            system_message='''Critic. Double check plan, claims, code from other agents and provide feedback. CTO should only send response in this format ```json[{"ComponentName": "", "filePath": ['full-file-path-1.py', 'full-file-path-2.py'], "content": "...."}]``` and nothing more''',
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, cto, critic], messages=[], max_round=5)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            })

        user_proxy.initiate_chat(
            manager,
            message=f"""This is the functional requirement for my application. Please create a solution design for this application. 
            Chief Product Officer has the following high-level requirement: ||{cpo_plan}||
            Product Manager has gathered more information for each of the feature as below: ||{product_manager_plan}||
            """
        )

        cto_message = None
        for message in reversed(groupchat.messages):
            if message['name'] == 'ChiefTechnologyOfficer' and message['content'] is not None:
                cto_message = message['content']
                break
        
        cto_plan = []
        if cto_message != "":
            # regex = r"```(?:json)?\s*\n?({.*?})\s*\n?```"
            regex = r"```(?:json)?\s*\n?(\[.*?\]|\{.*?\})\s*\n?```"
            matches = re.finditer(regex, cto_message, re.DOTALL)
            for match in matches:
                code = match.group(1).strip()
                if "CODE" in code:
                    continue
                cto_plan = json.loads(code)
                self.cto_plan = cto_plan
        else:
            print("CTO plan is not structured properly")


    def architect_solution(self, cpo_plan: dict, file_path: str, component_name: str, functional_requirement: str) -> None:
        cpo_plan = json.dumps(cpo_plan)

        config_list=[
            {
                "model": "gpt-3.5-turbo-16k",
                "api_key": os.environ.get("OPENAI_API_KEY")
            }
        ]

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },
            system_message = "User. Interact with the Project Manager to create a project plan. Final project break-down needs to be approved by this user.",
            code_execution_config=False,
        )

        cto = autogen.AssistantAgent(
            name = "SolutionsArchitect",
            llm_config = config_list,
            system_message = '''Solutions Architect. You are an expert software architect. You are an expert in Cloud, microservices and Python development. You analyze functional requirements thoroughly, review the <filestructure> recommendation from CTO, overall product vision from CPO.
            This application will be developed in Python.
            Write only the skeleton for each of the file based on CTO's recommendation.
            Your output should code block with each file name.
            '''
        )

        critic = autogen.AssistantAgent(
            name="Critic",
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            },
            system_message='''Critic. Double check plan, claims, code from other agents and provide feedback. Solutions Architect must have considered filestructure recommended by CTO. Solutions Architect must be giving code blocks with matching file names''',
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, cto, critic], messages=[], max_round=5)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": config_list,
            })

        user_proxy.initiate_chat(
            manager,
            message=f"""Please create skeleton for each files from recommendation from CTO as below: |||{file_path}|||. 
            ComponentName: |||{component_name}|||
            Chief Product Officer's plan is as below: |||{cpo_plan}|||
            This is the functional requirement from product manager: |||{functional_requirement}|||
            """
        )

        sa_message = None
        for message in reversed(groupchat.messages):
            if message['name'] == 'SolutionsArchitect' and message['content'] is not None:
                sa_message = message['content']
                break

        print("************************************")
        print(sa_message)
