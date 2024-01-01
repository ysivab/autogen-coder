import autogen

from typing import Dict, List

class Deployer:
    def __init__(self):
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )

    def start(self, user_persona: dict, expert_persona: dict) -> str:
        user_proxy = autogen.UserProxyAgent(
            name = user_persona['name'],
            # description = user_persona['description'],
            llm_config={
                "temperature": 0,
                "config_list": self.config_list,
            },
            # system_message = user_persona['system_message'],
            code_execution_config={
                "work_dir": "coding",
                "use_docker": False,  # set to True or image name like "python:3" to use docker
            },
            human_input_mode = user_persona['human_input_mode'],
            max_consecutive_auto_reply = 10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        )

        expert = autogen.AssistantAgent(
            name = expert_persona['name'], 
            # description = expert_persona['description'],
            llm_config={
                "temperature": 0,
                "config_list": self.config_list,
            },
        )

        user_proxy.initiate_chat(
            expert,
            message = user_persona['task']
        )
        # groupchat_result = groupchat.messages

        return "output"