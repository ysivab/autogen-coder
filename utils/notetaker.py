import autogen
import json

from typing import Dict, List

class NoteTaker:
    def __init__(self):
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )

    def summarize(self, task, seminar_notes: List[Dict]) -> str:
        seminar_notes = json.dumps(seminar_notes)
        # termination_msg = lambda x: isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()
        termination_msg = lambda x: isinstance(x, dict) and x.get("content", "").upper() == "TERMINATE"


        expert = autogen.AssistantAgent(
            name = "Expert",
            is_termination_msg=termination_msg,
            llm_config={
                "temperature": 0,
                "config_list": self.config_list,
            },
            system_message = '''Expert. You are an expert note taker in technical field.
            You are responsible for reviewing the discussion and performing the task asked by the user
            Reply `TERMINATE` in the end when everything is done.
            '''
        )

        user_proxy = autogen.UserProxyAgent(
            name = "User",
            is_termination_msg=termination_msg,
            llm_config={
                "config_list": self.config_list,
            },
            human_input_mode = "NEVER",
            max_consecutive_auto_reply = 0,
            code_execution_config=False,
            description = "This persona does not respond. It does not participate in this seminar."
            # default_auto_reply="Reply `TERMINATE` if the task is done.",
        )

        user_proxy.initiate_chat(
            expert,
            message=f"""
                You had a discussion with multiple people. You are an expert in this topic. Here's the meeting notes: <notes>{seminar_notes}</notes>
                {task}
                Reply `TERMINATE` if the task is done.
                """
        )
        # user_proxy.stop_reply_at_receive(software_architect)
        # user_proxy.send("TERMINATE", software_architect)

        summary = user_proxy.last_message()['content']
        
        return summary