import autogen
import re

from docx import Document

from utils.seminar import Seminar

class Plan:
    def __init__(self, config_type):
        self.requirements: str = None
        self.product_plan: str = None

        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )

        self.product_manager_constraints = '''
        You must follow all the rules below:
        Rule #1: Analze the entire requirement thoroughly and identify any gaps
        Rule #2: Don't make any assumptions on requirement. Ask the user to clarify.
        Rule #3: Always write the entirety of the plan.
        Rule #4: Capsulate the actual product functional requirement in <plan></plan>.
        ** IMPORTANT **
        Here's an example of a good response for your reference:
        As per the discussion, here's the final product requirement
        <plan>
        # intro
        # design etc etc.
        </plan>

        Here's an example of a bad response:
        <plan>
        As per the discussion, here's the final product requirement
        # intro
        # design etc etc.
        </plan>
        '''
    
    # check if document is valid and not empty
    # extract content and save it in requirements
    def read_requirements(self, doc_path) -> None:
        doc = Document(doc_path)
        self.requirements = '\n'.join([paragraph.text for paragraph in doc.paragraphs])


    # start seminar between agents
    def _start_seminar(self, human_input_mode) -> str:
        user_persona: dict = {
            "name": "User",
            "description": "This agent only responds once and then never speak again.",
            "system_message": "User. Interact with the Product Manager to discuss and finalize application requirement. Final decision needs to be approved by this user.",
            "human_input_mode": human_input_mode,
            "task": f"""
            This is my business requirement. Please write me a comprehensive product functional requirement for a technical implementation: " {self.requirements}
            You must follow these rules: {self.product_manager_constraints}
            """
        }

        expert_persona: dict = {
            "name": "ProductManager",
            "description": "This agent will be the first speaker and the last speaker in this seminar",
            "system_message": f'''Product Manager. You are an expert in Product Development. You analyze business requirements thoroughly and create a comprehensive product functional requirement. Functional requirement must include schema details for database, and other details.
            You must follow all these rules below:
            Rule #1: You will analyze the requirement, prepare questions and ask the user to clarify any requirement before finalizing the requirement.
            Rule #2: You will always rewrite the entire product functional requirement in if you are incorporating the feedback.
            Rule #3: Never make ambiguous statements. The functional requirement must be very clear and direct. 
            Rule #4: Capsulate the actual product functional requirement in <plan></plan>.
            '''
        }

        critic_persona: dict = {
            "name": "Critic",
            "description": "This agent only speaks once, and only after Software Developer to critique the work",
            "system_message": '''Critic. Double check plan, responses from other agents and provide feedback. 
            You must follow one rule: Always write the product functional requirement in <plan></plan> and return with your response. Not just the suggestion.''',
        }

        seminar: Seminar = Seminar()
        seminar_notes = seminar.start(user_persona, critic_persona, expert_persona)

        # find the last code block and send it as the source code
        product_plan: str = None
        for message in reversed(seminar_notes):
            pattern = r"<plan>(?:\w+)?\s*\n(.*?)\n</plan>"
            matches = re.findall(pattern, message['content'], re.DOTALL)
            
            # only one code block is expected. if there's no code block OR
            # if there are multiple code blocks, then human involve required
            if len(matches) == 1:
                product_plan = matches[0].strip()
                break                
            
        return product_plan
    

    # Review the word document and create high-level components
    def analyze_and_plan(self) -> None:
        seminar_result = self._start_seminar("ALWAYS")
        self.product_plan = seminar_result
