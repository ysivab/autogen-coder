import autogen
import json

from SDLC.plan import Plan
from SDLC.design import Design
from SDLC.develop import Develop

plan: Plan = Plan()
plan.read_requirements("/Users/brinthan/Desktop/Web Publishing System API Requirements Document.docx")
plan.analyze_and_plan()

design: Design = Design()
design.cto_consultation(plan.cpo_plan, plan.product_manager_plan)

# create a project plan combining product management and CTO's plans
project_plan = []
for cto_plan in design.cto_plan:
    component_name = cto_plan.get('ComponentName', '')
    project_item = {
        'ComponentName': component_name,
        'filePath': cto_plan.get('filePath', [])
    }
    
    for product_plan in plan.product_manager_plan:
        if product_plan.get('ComponentName') == component_name:
            project_item['FunctionalRequirement'] = product_plan.get('FunctionalRequirement', {})
            break
    
    project_plan.append(project_item)

for task in project_plan:
    component_name = task.get('ComponentName', '')

    files = task.get('filePath', ['Error'])
    all_files: str = None
    if files is not []:
        all_files = json.dumps(files)

    functional_requirement = task.get('FunctionalRequirement', {})
    if functional_requirement is not {}:
        functional_requirement = json.dumps(functional_requirement)

    if files is not []:
        for file in files:
            design.architect_solution(plan.cpo_plan, file, all_files, component_name, functional_requirement)



develop: Develop = Develop()
develop.root_folder = '/Users/brinthan/workspace/ml-learning/autogen-coder/coding/'
develop.source_code = design.source_code
develop.project_plan = project_plan
develop.write_code()


# for requirement in plan.product_manager_plan:
#     # component_name = requirement.get('ComponentName', {})
#     # functional_requirement = json.dumps(requirement.get('FunctionalRequirement', {}))
#     design.architect_solution(plan.cpo_plan, plan.product_manager_plan)

# for requirement in plan.detail_requirements:
#     print(requirement)
#     # design.requirements = json.dumps(requirement.get('FunctionalRequirement', {}))
    
#     print("******************************************")
#     print(design.generated_content)


# assistant = autogen.AssistantAgent(
#     name = "assistant"
# )

# user_proxy = autogen.UserProxyAgent(
#     name = "user_proxy",
#     human_input_mode = "ALWAYS",
#     code_execution_config={
#         "work_dir": "coding"
#     }
# )

# user_proxy.initiate_chat(
#     assistant,
#     message="""What date is today?"""
# )

# user_proxy = autogen.UserProxyAgent(
#     name = "Admin",
#     system_message = "A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin.",
#     code_execution_config=False,
# )

# engineer = autogen.AssistantAgent(
#     name = "Engineer",
#     system_message = '''Engineer. You follow an approved plan. You write python/shell code to solve tasks. Wrap the code in a code block that specifies the script type. The user can't modify your code. So do not suggest incomplete code which requires others to modify. Don't use a code block if it's not intended to be executed by the executor.
# Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. Check the execution result returned by the executor.
# If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
# '''
# )

# executor = autogen.UserProxyAgent(
#     name="Executor",
#     system_message="Executor. Execute the code written by the engineer and report the result.",
#     human_input_mode="NEVER",
#     code_execution_config={"last_n_messages": 3, "work_dir": "coding"},
# )

# critic = autogen.AssistantAgent(
#     name="Critic",
#     system_message="Critic. Double check plan, claims, code from other agents and provide feedback. Check whether the plan includes adding verifiable info such as source URL.",
#     # llm_config=gpt4_config,
# )

# groupchat = autogen.GroupChat(agents=[user_proxy, engineer, executor, critic], messages=[], max_round=5)
# manager = autogen.GroupChatManager(groupchat=groupchat)

# response = user_proxy.initiate_chat(
#     manager,
#     message="""
# Write me a hello world function in python.
# """,
# )

# critic_message = None
# for message in reversed(groupchat.messages):
#     if message['name'] == 'Critic' and message['content'] is not None:
#         critic_message = message['content']
#         break

# print(critic_message)