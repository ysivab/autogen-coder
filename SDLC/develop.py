import autogen
import os
import json
import re

from docx import Document
from utils.notetaker import NoteTaker
from utils.seminar import Seminar

class Develop:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}
        self.file_structure: str = None
        self.architecture_document: str = None


    # software developer to write code to the disk
    def _write_code_to_disk(self, file_path, code):
        # Extract directory path and file name
        file_path = os.path.join(self.root_folder, file_path)
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
        summary = notetaker.summarize("Revise the initial code block from the developer and incorporate feedback from the critic. Remove any duplicate information. Rewrite the code block by including user and critic's feedback", seminar_notes)

        # pattern = r"(?:\w+)?\s*\n?(.*?)\s*"
        pattern = r"```(?:\w+)?\s*\n(.*?)\n```"
        match = re.search(pattern, summary, re.DOTALL)

        if match:
            source_code = match.group(1).strip()
        else:
            source_code = "No viable code written"

        return source_code
    


    # software development phase
    def _development_seminar(self, file_path) -> str:
        user_persona: dict = {
                "name": "User",
                "description": "This agent only responds once and then never speak again.",
                "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
                "human_input_mode": "NEVER",
                "task": f"""
                Here's the full project structure for your reference <files>{self.file_structure}</files>. 
                Write the full code for only this specific file <file>{file_path} only to satisfy requirement on the <document> below.
                This is the architecture document <document>{self.architecture_document}</document>
                Do NOT write any other classes.
                """
            }
        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": '''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
            You will write the code for the specific file you've been asked to develop. Don't write any other files, only focus on your file.
            Your output should be strictly just one code block.
            '''
        }
        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Software Developer to critique the work",
            "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # remove the initial request, no need to send that
        seminar_notes = seminar_notes[1:]
        seminar_conclusion = self._summarizer(seminar_notes)

        print("#*#*#$()@#*$)(@*#$)(*@#)($*@)#($*)(@#$*)(@#$*)(@#*$)(#*$)")
        print(seminar_conclusion)

        return seminar_conclusion


    # look for place holders in code and write the function again
    def _placeholder_check(self, file_path) -> str:
        source_code = self.source_code[file_path]
        user_persona: dict = {
                "name": "User",
                "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
                "description": "This agent only responds once and then never speak again.",
                "human_input_mode": "NEVER",
                "task": f"""
                Here's the full project structure for your reference <files>{self.file_structure}</files>. 
                Review the entire code <code>{source_code}</code> for this file <file>{file_path}</file>.
                You must complete the entire code by completing any placeholder code to meet the requirement for the code below as per <document>.
                This is the architecture document <document>{self.architecture_document}</document>
                Do NOT write any other classes.
                """
            }
        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": '''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
            You will write the code for the specific file you've been asked to develop. Don't write any other files, only focus on your file.
            Your output should be strictly just one code block.
            '''
        }
        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Software Developer to critique the work",
            "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # remove the initial request, no need to send that
        seminar_notes = seminar_notes[1:]
        seminar_conclusion = self._summarizer(seminar_notes)

        return seminar_conclusion



    # handle entire code writing 
    def write_code(self) -> None:
        for file_path, code in self.source_code.items():
            seminar_notes = self._development_seminar(file_path)

            # if there's multiple code blocks or no code block at all, let's try development again
            matches = re.findall(r'```', seminar_notes)
            if len(matches) > 1 or len(matches) == 0:
                seminar_notes = self._development_seminar(file_path)
        
            # self.source_code[file_path] = self._summarizer(seminar_notes)
            self.source_code[file_path] = seminar_notes

            # code QA run to find any placeholder and remove
            seminar_notes =  self._placeholder_check(file_path)
            self.source_code[file_path] = self._summarizer(seminar_notes)



    # review code for integration
    def _validate_integration(self, file_path):
        seminar_conclusion: str = None
        source_code = self.source_code[file_path]
        all_code = json.dumps(self.source_code)

        user_persona: dict = {
                "name": "User",
                "description": "This agent only responds once and then never speak again.",
                "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
                "human_input_mode": "NEVER",
                "task": f"""
                Here's the full project source code for your reference <source_code>{all_code}</source_code>. 
                Review the entire code <code>{source_code}</code> for this file <file>{file_path}</file>.
                You must ensure your file is well written to integrate with rest of the application.
                Do NOT write any other classes.
                """
            }
        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker",
            "system_message": '''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
            You will review and ensure your file is connected well to integrate with rest of the application. Don't write any other files, only focus on your file.
            Your output should be strictly just one code block.
            '''
        }
        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speak after Software Developer and only once",
            "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # remove the product plan, no need to send that
        seminar_notes = seminar_notes[1:]
        
        seminar_conclusion = self._summarizer(seminar_notes)
        return seminar_conclusion

    # upload all code and check if any of them require modification
    def code_review(self) -> None:
        for file_path, code in self.source_code.items():
            seminar_notes = self._validate_integration(file_path)
            
            # if there's multiple code blocks or no code block at all, let's try development again
            matches = re.findall(r'```', seminar_notes)
            if len(matches) > 1 or len(matches) == 0:
                seminar_notes = self._development_seminar(file_path)
        
            self.source_code[file_path] = self._summarizer(seminar_notes)


    # save the code to local disk
    def save_code(self) -> None:
        for file_path, code in self.source_code.items():
            self._write_code_to_disk(file_path, code)


