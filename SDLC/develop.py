import autogen
import os
import json

from docx import Document

class Develop:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None
        self.root_folder: str = None
        self.product_manager_plan: dict = []
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
        for file_path, code in self.source_code.items():
            self._write_code_to_disk(file_path, code)

