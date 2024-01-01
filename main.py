import argparse
# import importlib

from SDLC.plan import Plan
from SDLC.design import Design
from SDLC.develop import Develop
from SDLC.integrate import Integrate
from SDLC.sandbox import Sandbox

parser = argparse.ArgumentParser()
parser.add_argument('--config', help='Configuration to use', required=True)
args = parser.parse_args()

config_type = args.config

plan: Plan = Plan(config_type)
# plan.read_requirements("/Users/brinthan/Desktop/Web Publishing System API Requirements Document.docx")
# plan.read_requirements("/Users/brinthan/Desktop/web-pub-2.docx")
plan.read_requirements("/Users/brinthan/Desktop/test-2.docx")
# plan.read_requirements("/Users/brinthan/Desktop/game-1.docx")
plan.analyze_and_plan()

design: Design = Design(config_type)
# design.cto_consultation(plan.product_plan)
design.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
design.architect_solution(plan.product_plan)

develop: Develop = Develop()
develop.source_code = design.source_code
develop.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
develop.project_structure = design.project_structure
develop.architecture_document = design.architecture_document
develop.config_type = config_type
develop.write_code()
# develop.code_review()
develop.save_code()

integrate: Integrate = Integrate()
integrate.source_code = develop.source_code
integrate.architecture_document = design.architecture_document
integrate.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
integrate.resolve_dependency()
integrate.map_resources()

sandbox: Sandbox = Sandbox()
sandbox.source_code_on_disk = integrate.source_code_on_disk
sandbox.cloud_stack_map = integrate.cloud_stack_map
sandbox.architecture_document = design.architecture_document
sandbox.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
sandbox.deploy_to_sandbox()

