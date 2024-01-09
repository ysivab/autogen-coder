import os
import importlib
import re

from utils.seminar import Seminar

class Develop:
    def __init__(self, config_type):
        self.config_type = config_type

         # load common configs
        common_module = importlib.import_module(f"config.{self.config_type}.common")
        self.language = getattr(common_module, 'language', "python")

        # load custom configs
        config_module = importlib.import_module(f"config.{self.config_type}.develop")
        self.developer_constraints = getattr(config_module, 'developer_constraints', None)
        self.critic_constraints = getattr(config_module, 'critic_constraints', None)

        self.root_folder: str = None
        self.source_code: dict = {}
        self.project_structure: str = None
        self.architecture_document: str = None


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


    # software development phase
    def _development_seminar(self, file_path, human_input_mode="NEVER") -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Software Developer to help a implement the function. Final project break-down needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            Here's the full project structure for your reference <project-structure>{self.project_structure}</project-structure>. 
            Write the full code for only this specific component {file_path} only to satisfy requirement on the <document> below.
            You must follow these rules: {self.developer_constraints}
            This is the architecture document <document>{self.architecture_document}</document>
            Do NOT write any other classes.
            """
        }

        expert_persona: dict = {
            "name": "SoftwareDeveloper",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''Software Developer. You are part of a group of expert {self.language} software developers. You analyze full functional requirements thoroughly.
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
            "system_message": f'''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.
            You must follow one rule: Always write the entire code and return with your response. Not just the suggestion.
            {self.critic_constraints}
            ''',
            
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


    # handle entire code writing 
    def write_code(self) -> None:
        for file_path, code in self.source_code.items():
            seminar_notes = self._development_seminar(file_path)

            # validate the code block
            # involve human if no code block or if there are multiple code blocks
            if seminar_notes is None:
                seminar_notes = self._development_seminar(file_path, "ALWAYS")

            self.source_code[file_path] = seminar_notes


    # save the code to local disk
    def save_code(self) -> None:
        for file_path, code in self.source_code.items():
            self._write_code_to_disk(file_path, code)


