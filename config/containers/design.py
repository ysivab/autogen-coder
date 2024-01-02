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

project_structure_rules ='''Extract full file paths for this project.
    You must follow this rule:
    Rule #1: You must give your response in <response></response>
    Rule #2: You must have only the file name in the <respone>. Other texts should never be inside <response>

    ** Important **
    Here's an example of bad response
    <response>
    here are some files based on analysis
    file1
    file2
    file3
    </response>

    Here's an example of a good response
    Here's the file structure based on analysis
    <response>
    file1
    </response>
'''
