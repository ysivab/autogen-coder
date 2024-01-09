import argparse
import os

from workflow import run_deploy, run_workflow

parser = argparse.ArgumentParser()
parser.add_argument('--config', help='Configuration to use', required=True)
parser.add_argument('--workspace', help='Workspace directory for code and other files', required=False)
parser.add_argument('--requirement-doc', help='Requirement document in word', required=False)
parser.add_argument('--architecture-doc', help='Technical architecture document in .MD file', required=False)
parser.add_argument('--task', help='Implementation request', required=False)
parser.add_argument('--project-name', help='Project name', required=True)
parser.add_argument('--deploy-only', required=False, help='Run deployment tasks only')


args = parser.parse_args()

if args.deploy_only:
    if os.path.exists(args.deploy_only):
        run_deploy(args)
    else:
        parser.error(f"--deploy-only template doesn't exist in this pasth {args.deploy_only}")
else:
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

    run_workflow(args)


