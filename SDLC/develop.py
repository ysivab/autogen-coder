import autogen
import os
import json

from docx import Document

class Design:
    def __init__(self):
        self.generated_content: str = None
        self.requirements: str = None


    # software developer to write code for each file
    