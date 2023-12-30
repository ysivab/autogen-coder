import autogen
import os
import json
import re

from utils.seminar import Seminar

class Develop:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}
        self.project_structure: str = None
        self.architecture_document: str = None

        self.serverless: bool = True
        self.developer_constraints = '''
            Rule #1: Never write any other class than what you are asked to do in this case.
            Rule #2: Other classes and files will be written by other developors
            Rule #3: Never leave placeholders. Always implement the functionality
            Rule #4: Review the architecture document carefully and understand what this exact function is supposed to do.
            Rule #5: Ensure this file / class is connected to the rest of the application through recommendation from Architecture Document.
            Rule #6: Think step by step, and then review the overall cohesion with the architecture document before writing this specific file / class.
            Rule #7: Never forget rule # 1. Don't write other classes or files. Only focus on the current file.
            Rule #8: Always respond with the entirety of the code. Not just the feedback or suggestion.
        '''

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


    # check for response and summarize
    # def _summarizer(self, seminar_notes) -> str:
    #     source_code: str = None

    #     notetaker: NoteTaker = NoteTaker()
    #     summary = notetaker.summarize('''Revise the initial code block from the developer and incorporate feedback from the critic. Remove any duplicate information. Rewrite the code block by including user and critic's feedback.
    #     You must follow these rules:
    #     Rule #1: Note down the first response and the speaker.
    #     Rule #2: Review each feedback. If there's concurrence, then make the adjustment on the first response.
    #     Rule #3: Never drop the first response. Keep adjusting the first response for each feedback.
    #     Rule #4: You must never have more than one code block in your response.
    #     ** Important ***
    #     Example of a Bad output:
    #     initial code
    #     ```
    #     # code
    #     ```
    #     revised code
    #     ```
    #     # code
    #     ```

    #     Example of a Good output:
    #     Revised code
    #     ```
    #     # code
    #     ```
        
    #     ''', seminar_notes)

    #     # pattern = r"(?:\w+)?\s*\n?(.*?)\s*"
    #     pattern = r"```(?:\w+)?\s*\n(.*?)\n```"
    #     match = re.search(pattern, summary, re.DOTALL)

    #     if match:
    #         source_code = match.group(1).strip()
    #     else:
    #         source_code = "No viable code written"

    #     return source_code
    


    # software development phase
    def _development_seminar(self, file_path, human_input_mode="NEVER") -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Here's the full project structure for your reference <project-structure>{self.project_structure}</project-structure>. 
            Write the full code for only this specific component <component>{file_path}</component> only to satisfy requirement on the <document> below.
            You must follow these rules: {self.developer_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            Do NOT write any other classes.
            """
        }

        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
            You must follow all these rules below:
            Rule #1: You will write the code for the specific component you've been asked to develop. Don't write any other components, only focus on your component.
            Rule #2: Your output should be strictly just one code block.
            Rule #3: You will always rewrite the entire code and return in your response.
            Rule #4: Never leave any placeholder code, or sample code or "test" values. The code must be ready for production.
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Software Developer to critique the work",
            "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.
            You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.''',
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


    # # look for place holders in code and write the function again
    # def _placeholder_check(self, file_path, human_input_mode="NEVER") -> str:
    #     source_code = self.source_code[file_path]
    #     user_persona: dict = {
    #             "name": "User",
    #             "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
    #             "description": "This agent only responds once and then never speak again.",
    #             "human_input_mode": human_input_mode,
    #             "task": f"""
    #             Here's the full project structure for your reference <project-structure>{self.project_structure}</project-structure>. 
    #             Review the entire code <code>{source_code}</code> for this component <component>{file_path}</component>.
    #             You must complete the entire code by completing any placeholder code to meet the requirement for the code below as per <document>.
    #             This is the architecture document <document>{self.architecture_document}</document>
    #             Do NOT write any other classes.
    #             """
    #         }
    #     expert_persona: dict = {
    #         "name": "SoftwareDeveloper",
    #         "description": "This agent will be the first speaker and the last speaker in this seminar",
    #         "system_message": '''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
    #         You will write the code for the specific component you've been asked to develop. Don't write any other components, only focus on your component.
    #         Your output should be strictly just one code block.
    #         '''
    #     }
    #     critic_persona: dict = {
    #         "name": "Critic",
    #         "description": "This agent only speaks once, and only after Software Developer to critique the work",
    #         "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
    #     }

    #     seminar: Seminar = Seminar()
    #     seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

    #     # remove the initial request, no need to send that
    #     seminar_notes = seminar_notes[1:]
    #     seminar_conclusion = self._summarizer(seminar_notes)

    #     return seminar_conclusion



    # handle entire code writing 
    def write_code(self) -> None:
        for file_path, code in self.source_code.items():
            seminar_notes = self._development_seminar(file_path)

            # validate the code block
            # involve human if no code block or if there are multiple code blocks
            if seminar_notes is None:
                seminar_notes = self._development_seminar(file_path, "ALWAYS")
            else:
                print("CODE SUCCESS #*(#$*)(#*$()@*#$)(*@#)$(*@#)($*)@#(*$()@#*$)(*@#$)(*@#$)(*@#)($*)@(#$*)@(#$*@#$)(*)")
            # if there's multiple code blocks or no code block at all, let's try development again
            # matches = re.findall(r'```', seminar_notes)
            # if len(matches) > 1 or len(matches) == 0:
            #     seminar_notes = self._development_seminar(file_path)
        
            # self.source_code[file_path] = self._summarizer(seminar_notes)
            self.source_code[file_path] = seminar_notes

            # code QA run to find any placeholder and remove
            # seminar_notes =  self._placeholder_check(file_path)
            # self.source_code[file_path] = seminar_notes
            # self.source_code[file_path] = self._summarizer(seminar_notes)



    # # review code for integration (OPTIONAL)
    # def _validate_integration(self, file_path):
    #     seminar_conclusion: str = None
    #     source_code = self.source_code[file_path]
    #     all_code = json.dumps(self.source_code)

    #     user_persona: dict = {
    #             "name": "User",
    #             "description": "This agent only responds once and then never speak again.",
    #             "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
    #             "human_input_mode": "NEVER",
    #             "task": f"""
    #             Here's the full project source code for your reference <source_code>{all_code}</source_code>. 
    #             Review the entire code <code>{source_code}</code> for this component <component>{file_path}</component>.
    #             You must ensure your file is well written to integrate with rest of the application.
    #             Do NOT write any other classes.
    #             """
    #         }
    #     expert_persona: dict = {
    #         "name": "SoftwareDeveloper",
    #         "description": "This agent will be the first speaker and the last speaker",
    #         "system_message": '''Software Developer. You are part of a group of expert Python software developers. You analyze full functional requirements thoroughly.
    #         You will review and ensure your component is connected well to integrate with rest of the application. Don't write any other components, only focus on your component.
    #         Your output should be strictly just one code block.
    #         '''
    #     }
    #     critic_persona: dict = {
    #         "name": "Critic",
    #         "description": "This agent only speak after Software Developer and only once",
    #         "system_message": '''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
    #     }

    #     seminar: Seminar = Seminar()
    #     seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

    #     # remove the product plan, no need to send that
    #     seminar_notes = seminar_notes[1:]
        
    #     seminar_conclusion = self._summarizer(seminar_notes)
    #     return seminar_conclusion

    # # upload all code and check if any of them require modification
    # def code_review(self) -> None:
    #     for file_path, code in self.source_code.items():
    #         seminar_notes = self._validate_integration(file_path)
            
    #         # if there's multiple code blocks or no code block at all, let's try development again
    #         matches = re.findall(r'```', seminar_notes)
    #         if len(matches) > 1 or len(matches) == 0:
    #             seminar_notes = self._development_seminar(file_path)
        
    #         self.source_code[file_path] = self._summarizer(seminar_notes)


    # save the code to local disk
    def save_code(self) -> None:
        for file_path, code in self.source_code.items():
            self._write_code_to_disk(file_path, code)


