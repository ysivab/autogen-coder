integration_constraints = '''
    - This is for Containers
    - User cannot read text. You must ensure format is in a codeblock with the filename for the dependency
'''

sandbox_constraints = '''
    You must follow all of these rules:
    Rule #1: First read the entire architecture document and create a high-level plan
    Rule #2: Determine the number of containers to be created
    Rule #4: Troubleshoot the issue until all resources are deployed.
'''

devops_constraints = '''
    You must follow these rules:
    Rule #1: Don't create any resources that are not mentioned in the architecture document
    Rule #2: Never leave any placeholders or test code in your template.
    Rule #3: Entire template must be ready for production release
    Rule #4: Review the template at least 5 times for syntax errors, consistencies, and integration
'''

rules_identify_dependencies = '''
    ** IMPORTANT **
    You must strictly follow all the rules listed below.
    Rule #1
    Never install any packages that are already part of basic Python installation

    Rule #2
    You must provide the response in single code block.
    Here's an examples of poorly written response:
    ** poor response**
    text text text
    ```
    import boto3
    ```
    text text text
    ```
    do this next
    ```

    Here's an examples of good response for Python:
    ** good response ***
    ```requirements.txt
    boto3
    ```
'''

rules_identify_resources = '''
    ** IMPORTANT **
    You must follow all of these rules
    Rule #1: Identify the resource, and description. Include both in your response.
    Rule #2: You must encapsulate resource details only in <response></response>

    Few examples of a bad response
    <response>
    After reviewing the document, AWS API Gateway is required. 
    AWS API Gateway provides an endpoint for the application.
    </response>

    Example of a good resposne
    After reviewing the document, AWS API Gateway is required. 
    AWS API Gateway provides an endpoint for the application.
    <response>
    2 AWS API Gateways are required.
    AWS API # 1: Purpose of this API Gateway is to provide an endpoint for Content Management for public access. The following lambdas will be receiving traffic through this API Gateway - viewArticles, viewmembers, SearchArticles
    AWS API #2: This API needs to be secured with AWS Cognito. The following lambdas will be receicing traffic through this API - AddMember, AddArticle, RemovArticle
    </response>
    Other details details balh blah
'''