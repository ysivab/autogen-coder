import autogen
import os
import json
import sys
import re
from typing import Dict, List

from docx import Document

class Plan:
    def __init__(self):
        self.requirements: str = None
        self.product_plan: str = None

        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )
    
    # check if document is valid and not empty
    # extract content and save it in requirements
    def read_requirements(self, doc_path) -> None:
        doc = Document(doc_path)
        self.requirements = '\n'.join([paragraph.text for paragraph in doc.paragraphs])


    # start seminar between agents
    def _start_seminar(self) -> List[Dict]:
        termination_msg = lambda x: isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            is_termination_msg=termination_msg,
            llm_config={
                "config_list": self.config_list,
            },
            system_message = "User. Interact with the Chief Product Officer and Product Manager to discuss the requirement. Final project break-down needs to be approved by this user.",
            code_execution_config=False,
            human_input_mode = "NEVER",
            default_auto_reply="Reply `TERMINATE` if the task is done.",
        )

        cpo = autogen.AssistantAgent(
            name = "ChiefProductOfficer",
            is_termination_msg=termination_msg,
            llm_config={
                "config_list": self.config_list,
            },
            system_message = '''CPO. You are an expert in complex product development. You analyze business requirements from the user, and double check the plan from ProductManager.
            If necessary, provide feedback to Product Manager to improve the plan.
            If the user provides any feedback, review the feedback with the business requirement thoroughly and send the instruction to Product Manager.
            Do not write the plan yourself. You are responsible only to critic the work of Product Manager.
            Reply `TERMINATE` in the end when everything is done.
            '''
        )

        product_manager = autogen.AssistantAgent(
            name = "ProductManager",
            is_termination_msg=termination_msg,
            llm_config={
                "config_list": self.config_list,
            },
            system_message = '''ProductManager. You are an expert in Product Development. You analyze business requirements thoroughly and create a comprehensive product functional requirement. Functional requirement must include schema details for database, and other details.            
            You MUST revise the plan based on feedback from CPO, and user until user approval. You must also send the plan in this format:
            <feature: name>
            # your plan
            </feature>
            '''
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, product_manager, cpo, product_manager], messages=[], max_round=5, speaker_selection_method="round_robin", allow_repeat_speaker=False)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                # "temperature": 0,
                "config_list": self.config_list,
            },)

        user_proxy.initiate_chat(
            manager,
            message="This is my business requirement. Please write me a comprehensive product functional requirement for a technical implementation: " + self.requirements,
        )

        return groupchat.messages
    

    # summarize seminar result and get the final plan
    def _summarize(self, seminar_result: List[Dict]) -> str:
        seminar_result = json.dumps(seminar_result)
        termination_msg = lambda x: isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

        product_manager = autogen.AssistantAgent(
            name = "ProductManager",
            is_termination_msg=termination_msg,
            llm_config={
                "temperature": 0,
                "config_list": self.config_list,
            },
            system_message = '''Product Manager. You are an expert Product Manager.
            You will review the requirement from the user and capture product features.
            You must send the plan in this format:
            <feature: name>
            # your plan
            </feature>
            Reply `TERMINATE` in the end when everything is done.
            '''
        )

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            is_termination_msg=termination_msg,
            llm_config={
                "timeout": 600,
                "cache_seed": 42,
                "model": "gpt-3.5-turbo-16k",
                "config_list": self.config_list,
            },
            human_input_mode = "NEVER",
            code_execution_config=False,
            default_auto_reply="Reply `TERMINATE` if the task is done.",
        )

        user_proxy.initiate_chat(
            product_manager,
            message=f"""
                You had a discussion with multiple people for a product and captured the notes here. Participants in this meeting is discussing over multiple <feature> for a product.: <notes>{seminar_result}</notes>
                Summarize these notes and write the final product features.
                """
        )

        product_plan = user_proxy.last_message()['content']
        
        return product_plan
    

    # Review the word document and create high-level components
    def analyze_and_plan(self) -> None:
        seminar_result = self._start_seminar()
        product_plan = self._summarize(seminar_result)

        self.product_plan = product_plan


        
