import autogen
import json

from SDLC.plan import Plan
from SDLC.design import Design
from SDLC.develop import Develop

plan: Plan = Plan()
# plan.read_requirements("/Users/brinthan/Desktop/Web Publishing System API Requirements Document.docx")
plan.read_requirements("/Users/brinthan/Desktop/web-pub-2.docx")
# plan.read_requirements("/Users/brinthan/Desktop/game-1.docx")
plan.analyze_and_plan()

design: Design = Design()
# design.cto_consultation(plan.product_plan)
design.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
design.architect_solution(plan.product_plan)

develop: Develop = Develop()
develop.source_code = design.source_code
develop.root_folder = "/Users/brinthan/workspace/ml-learning/demo/autogen"
develop.file_structure = design.file_structure
develop.architecture_document = design.architecture_document
develop.write_code()
develop.code_review()
develop.save_code()
