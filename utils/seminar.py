import autogen

from typing import Dict, List

class Seminar:
    def __init__(self):
        self.config_list = autogen.config_list_from_json(
            "notebook/OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-3.5-turbo-16k"]
            },
        )

    def start(self, user_persona: dict, expert_persona: dict, critic_persona: dict, config=None) -> str:
        if config is None:
            config = self.config_list

        user_proxy = autogen.UserProxyAgent(
            name = user_persona['name'],
            description = user_persona['description'],
            llm_config={
                # "temperature": 0,
                "config_list": config,
            },
            system_message = user_persona['system_message'],
            code_execution_config=False,
            human_input_mode = user_persona['human_input_mode'],
            max_consecutive_auto_reply = 1
        )

        critic = autogen.AssistantAgent(
            name = critic_persona['name'],
            description = critic_persona['description'],
            llm_config={
                # "temperature": 0,
                "config_list": config,
            },
            system_message = critic_persona['system_message']
        )

        expert = autogen.AssistantAgent(
            name = expert_persona['name'], 
            description = expert_persona['description'],
            llm_config={
                # "temperature": 0,
                "config_list": config,
            },
            system_message = expert_persona['system_message']
        )
# speaker_selection_method="round_robin", 
        groupchat = autogen.GroupChat(agents=[user_proxy, expert, critic], messages=[], max_round=10, allow_repeat_speaker=False)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={
                # "temperature": 0,
                "config_list": config,
            },)

        user_proxy.initiate_chat(
            manager,
            message = user_persona['task']
        )
        groupchat_result = groupchat.messages

        return groupchat_result