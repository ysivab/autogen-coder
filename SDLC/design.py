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
        self.file_structure: str = None
        self.notetaker: NoteTaker = NoteTaker()

        # setting variables
        self.language: str = "Python"
        self.cloud: str = "AWS"
        self.cloud_services: str = "Containers, S3, IAM, SSM, DynamoDB"
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )
    
    # analyzes the high level requirement and detailed requirement to come up with technical guidance
    def _cto_consultation(self, product_manager_plan: str) -> str:
        # final architecture document
        architecture_document: str = None
        
        # combination of all notes from architecture component discussion
        note_collection: str = ''

        architecture_components = [
            {"phase": "high-level summary", "constraints": "Create a summary within 300 words. Do NOT discus any other details."},
            {"phase": "file and folder structure", "constraints": "Determine a very detailed file and folder structure. Do NOT discus any other details."},
            {"phase": "database requirement and design", "constraints": '''Application will be deployed in {self.cloud} with the following services {self.cloud_services}. Do NOT discus any other details that database schema and requirements.'''},
            {"phase": "cloud infrastructure design", "constraints": '''Application will be deployed in {self.cloud} with the following services {self.cloud_services}. Do not talk about CI/CD, networking or basic infrastructure. Do NOT discus any other details.'''}
        ]

        for component in architecture_components:
            phase = component['phase']
            constraints = component['constraints']
            user_persona: dict = {
                "name": "User",
                "description": "This agent only responds once and then never speak again.",
                "system_message": "User. Interact with the Software Architect to discuss the requirement. Final project break-down needs to be approved by this user.",
                "human_input_mode": "TERMINATE",
                "task": f"""
                Software Architect, I want you to determine the <task>{phase}</task> with the following constraints <constraint>{constraints}</constraints>. Do not discuss any other items.
                Product Manager has the following high-level requirement for my application: <plan>{product_manager_plan}</plan>.
                """
            }
            
            critic_persona: dict = {
                "name": "Critic",
                "description": "This agent speaks after Software Architect's response. CTO critique the work done by Software Architect and provides feedback.",
                "system_message": f'''Critic. You will review SoftwareArchitect's response and compare it with user's request. Only review {phase} and nothing more.
                Ensure you follow this rule: {constraints}
                Programming language to be used: {self.language}.
                Cloud services to be used: {self.cloud_services}
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

            # remove the product plan, no need to send that
            seminar_notes = seminar_notes[1:]

            notetaker: NoteTaker = NoteTaker()
            summary = notetaker.summarize("Revise the initial response from Software Architect and incorporate feedback from other speakers. Remove any duplicate information. Rewrite this in a formal 3rd party point of view.", seminar_notes)

            note_collection = note_collection + '\n' + summary

        notetaker: NoteTaker = NoteTaker()
        architecture_document = notetaker.summarize("Create an architecture.md file based on these notes. DO NOT SUMMARIZE ", note_collection)

        # write to disk
        file_path = os.path.join(self.root_folder, 'architecture-design.md')
        with open(file_path, 'w') as file:
            file.write(architecture_document)
        
        return architecture_document

    # extract a project plan
    # project plan should be specific instructions to the developers to execute
    # it should be split by files, and other common instructions
    def _create_project_structure(self) -> str:
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
            system_message = '''Software Developer. You are an expert Software Developer specializing in Python.
            You will review the architecture document and extract the recommended project structure.
            <files>
            full path of the file
            </files>
            Revise the project structure based on feedback from user. Redraw the entire <files> in each response.
            '''
        )

        groupchat = autogen.GroupChat(agents=[user_proxy, software_developer], messages=[], max_round=3)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                # "temperature": 0,
                "config_list": self.config_list,
            },)

        user_proxy.initiate_chat(
            manager,
            message=f"""Extract full file paths (in this format <files>full path</files>) for this project from this architecture document: <document>{self.architecture_document}</document>
            """
        )

        project_structure = None
        for message in reversed(groupchat.messages):
            if message['name'] == 'SoftwareDeveloper' and message['content'] is not None:
                project_structure = message['content']
                break
        
        return project_structure
            


    def architect_solution(self, product_manager_plan: str) -> None:
        seminar_result = self._cto_consultation(product_manager_plan)

        self.architecture_document = seminar_result

        project_structure = self._create_project_structure()
        self.file_structure = project_structure

        file_paths = project_structure.strip().split("\n")[1:-1]

        # initiate source code dict
        for file_path in file_paths:
            self.source_code[file_path] = ""

        print("**** Solution Design Completed ***")