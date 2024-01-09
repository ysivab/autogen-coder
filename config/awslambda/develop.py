developer_constraints = '''
    Rule #1: Never write any other class than what you are asked to do in this case.
    Rule #2: Other classes and files will be written by other developors
    Rule #3: Never leave placeholders. Always implement the functionality
    Rule #4: Review the architecture document carefully and understand what this exact function is supposed to do.
    Rule #5: Ensure this file / class is connected to the rest of the application through recommendation from Architecture Document.
    Rule #6: Think step by step, and then review the overall cohesion with the architecture document before writing this specific file / class.
    Rule #7: Never forget rule # 1. Don't write other classes or files. Only focus on the current file.
    Rule #8: Always respond with the entirety of the code. Not just the feedback or suggestion.
    Rule #9: Python Lambda handler must be 'index.lambda_handler'.
'''

critic_constraints = '''
    You must follow all these rules:
    Rule #1: Check the code and make sure all dependencies are delcared on the top
    Rule #2: Ensure Lambda handler is properly defined as 'index.lambda_handler'
'''


