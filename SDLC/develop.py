import autogen
import os
import json
import re

from docx import Document

class Develop:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.project_plan: dict = []
        self.source_code: dict = {}


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


    # ask software developer to review and write the code
    def write_code(self) -> None:
        for task in self.project_plan:
            file_path = task.get('filePath', '')
            functional_requirement = task.get('FunctionalRequirement', {})
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print(functional_requirement)
            for file in file_path:
                file_source_code = self.source_code[file]
                print("%%%%%%%%%%%%%%%%%%%%%%")
                print(functional_requirement)
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

                developer = autogen.AssistantAgent(
                    name = "SoftwareDeveloper",
                    llm_config = config_list,
                    system_message = '''Software Developer. You are an expert software developer in Python. You analyze functional requirements thoroughly, review the existing source code.
                    You will write missing functions, and write any placeholders.
                    Your output should be strictly just one code block.
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
                    system_message='''Critic. Double check plan, claims, code from other agents and provide feedback. Softwar Developer must return the output in just one code block.''',
                )

                groupchat = autogen.GroupChat(agents=[user_proxy, developer, critic], messages=[], max_round=5)
                manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                        "timeout": 600,
                        "cache_seed": 42,
                        "model": "gpt-3.5-turbo-16k",
                        "config_list": config_list,
                    })

                user_proxy.initiate_chat(
                    manager,
                    message=f"""
                    This is the code you are going to fix: ```{file_source_code}```
                    Purpose of this code is to implement the functionality: ```{functional_requirement}```
                    Write the full code for this specific class only to satisfy requirement of this class.
                    Do NOT write any other classes.
                    """
                )

                developer_message = None
                for message in reversed(groupchat.messages):
                    if message['name'] == 'SoftwareDeveloper' and message['content'] is not None:
                        developer_message = message['content']
                        break   

                if developer_message != "":
                    # regex = r"```(?:json)?\s*\n?({.*?})\s*\n?```"
                    regex = r"```python\s*\n?(.*?)\n?```"
                    matches = re.finditer(regex, developer_message, re.DOTALL)
                    for match in matches:
                        code = match.group(1).strip()
                        if "CODE" in code:
                            continue
                        self.source_code[file] = code
                else:
                    print("Software Developer response is not structured properly")

        # write the source code to local file
        for file_path, code in self.source_code.items():
            self._write_code_to_disk(file_path, code)

