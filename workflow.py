from utils.envprep import EnvPrep
from SDLC.plan import Plan
from SDLC.design import Design
from SDLC.develop import Develop
from SDLC.integrate import Integrate
from SDLC.deploy import Deploy


def _prep_env(args) -> str:
    # prepare environment
    env_prep = EnvPrep()
    project_path = env_prep.initiate(args.project_name, args.workspace)

    return project_path


def run_deploy(args):
    deploy: Deploy = Deploy(args.config)
    deploy.project_name = args.project_name
    deploy.read_deployment_template(args.deploy_only)
    deploy.deploy_to_sandbox()


# def run_plan(args):


def run_workflow(args):
    project_path = _prep_env(args)

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


    # Integrate stage
    integrate: Integrate = Integrate(args.config)
    # pass the data from previous stages
    integrate.source_code = develop.source_code
    integrate.architecture_document = design.architecture_document
    integrate.root_folder = project_path
    # resolve all package dependencies and map out resources to be deployed
    integrate.resolve_dependency()
    integrate.map_resources()


    deploy: Deploy = Deploy(args.config)
    deploy.project_name = args.project_name
    deploy.source_code = develop.source_code
    deploy.architecture_document = design.architecture_document
    deploy.root_folder = project_path
    deploy.infra_stack_map = integrate.infra_stack_map
    deploy.source_code_uri = integrate.source_code_uri
    deploy.deploy_to_sandbox()