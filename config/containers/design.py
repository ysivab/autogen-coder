architecture_components = [
    {
        "phase": "high-level summary",
        "constraints": '''Create a summary within 300 words. Do NOT discus any other details.
        You must follow all these rules:
        Rule #1: Must encapsulate the actual summary in <response></response>.
        ** IMPORTANT **
        Here's an example of a good response:
        Based on the analysis, here's the high-level requirement:
        <response>
            # high level requirement
        </response>

        Here's an example of a bad response:
        <response>
            Based on the analysis, here's the high-level requirement:
            # high level requirement
        </response>
        '''
    },
    {
        "phase": "file and folder structure", 
        "constraints": '''Determine a very detailed file and folder structure. Do NOT discus any other details.
        You must follow all these rules:
        Rule #1: Must encapsulate the actual summary in <response></response>.
        ** IMPORTANT **
        Here's an example of a good response:
        Based on the analysis, here's the high-level requirement:
        <response>
            # high level requirement
        </response>

        Here's an example of a bad response:
        <response>
            Based on the analysis, here's the high-level requirement:
            # high level requirement
        </response>
        '''
    },
    {
        "phase": "database requirement and design", 
        "constraints": '''Application will be deployed on AWS with the following services containers. Do NOT discus any other details that database schema and requirements.
        You must follow all these rules:
        Rule #1: Must encapsulate the actual summary in <response></response>.
        ** IMPORTANT **
        Here's an example of a good response:
        Based on the analysis, here's the high-level requirement:
        <response>
            # high level requirement
        </response>

        Here's an example of a bad response:
        <response>
            Based on the analysis, here's the high-level requirement:
            # high level requirement
        </response>
        '''
    },
    {
        "phase": "infrastructure design", 
        "constraints": '''Application will be deployed on Kubernetes as containers. Do not talk about CI/CD, networking or basic infrastructure. Do NOT discus any other details.
        You must follow all these rules:
        Rule #1: Must encapsulate the actual summary in <response></response>.
        ** IMPORTANT **
        Here's an example of a good response:
        Based on the analysis, here's the high-level requirement:
        <response>
            # high level requirement
        </response>

        Here's an example of a bad response:
        <response>
            Based on the analysis, here's the high-level requirement:
            # high level requirement
        </response>
        '''
    }
]

project_structure_rules = [
    '''Extract full file paths (in this format 
    <response>
    full path
    </response>)'''
]