import argparse
import os

from utils.envprep import EnvPrep

from SDLC.plan import Plan
from SDLC.design import Design
from SDLC.develop import Develop
from SDLC.integrate import Integrate
from SDLC.sandbox import Sandbox

parser = argparse.ArgumentParser()
parser.add_argument('--config', help='Configuration to use', required=True)
parser.add_argument('--project-root', help='Output of code and other files', required=True)
parser.add_argument('--requirement-doc', help='Requirement document in word', required=False)
parser.add_argument('--architecture-doc', help='Technical architecture document in .MD file', required=False)
parser.add_argument('--task', help='Implementation request', required=False)
parser.add_argument('--project-name', help='Project name', required=True)

args = parser.parse_args()

# Validate requirement-doc extension
if args.requirement_doc and not args.requirement_doc.lower().endswith(('.doc', '.docx')):
    parser.error("--requirement-doc must end in '.doc' or '.docx'")

# Check if either requirement-doc or task is provided
if not args.requirement_doc and not args.task and not args.architecture_doc:
    parser.error("Only one of these must be provided: --requirement-doc or --task or --architecture-doc.")

# check if requirement doc needs to be used that it exist
if args.requirement_doc and not os.path.exists(args.requirement_doc):
    parser.error(f"--requirement-doc doesn't exist in this path {args.requirement_doc}")

# if architecture document to be used, verify it exists
if args.architecture_doc and not os.path.exists(args.architecture_doc):
    parser.error(f"--requirement-doc doesn't exist in this path {args.architecture_doc}")


# prepare environment
env_prep = EnvPrep()
project_path = env_prep.initiate(args.project_name, args.project_root)

plan = Plan(args.config)
design: Design = Design(args.config)

# if architecture document is presented, Planning and Design stages can be skipped
if not args.architecture_doc:
    # Set requirements or task for the plan
    if args.requirement_doc:
        plan.read_requirements(args.requirement_doc)
    else:
        plan.set_task(args.task)

    # Proceed with plan analysis
    plan.analyze_and_plan()

    # initiate and complete the architecture document
    design.root_folder = project_path
    # design a suitable technical architecture
    design.architect_solution(plan.product_plan)
else:
    # load architecture doc from file
    design.read_architecture_doc(args.architecture_doc)
    # create the project structure
    design.create_project_structure()


develop: Develop = Develop(args.config)
# pass the data from previous stages
develop.source_code = design.source_code
develop.root_folder = project_path
develop.project_structure = design.project_structure
develop.architecture_document = design.architecture_document
#write and save code to local diskc
develop.write_code()
develop.save_code()


# # Integrate stage
# integrate: Integrate = Integrate()

# integrate.source_code = develop.source_code
# integrate.architecture_document = design.architecture_document
# integrate.root_folder = project_path
# # resolve all package dependencies and map out resources to be deployed
# integrate.resolve_dependency()
# integrate.map_resources()

# sandbox: Sandbox = Sandbox()
# sandbox.source_code_on_disk = integrate.source_code_on_disk
# sandbox.cloud_stack_map = integrate.cloud_stack_map
# sandbox.architecture_document = design.architecture_document
# sandbox.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
# sandbox.deploy_to_sandbox()

