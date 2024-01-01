architecture_components = [
    {
        "phase": "high-level summary", 
        "constraints": '''You must follow ALL of these rules: 
            Rule #1: Create a summary within 300 words.
            Rule #2: Never any other details.
            Rule #3: Must encapsulate the actual summary in <response></response>.
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
        "phase": "AWS cloud components for this application", 
        "constraints": '''
            ALL of these rules must be followed:
            Rule #1: Only use these services where necessary - API Gateway, Lambda, DynamoDB, S3, SSM, SecurityGroup, IAM, and CloudWatch.
            Rule #2: Never discuss any other details
            Rule #3: Must encapsulate the actual summary in <response></response>.
            Rule #4: There should be no generic descriptions for each of these services.
            Rule #5: Each services must be evaluated against the overall plan and functional requirements to ensure whether they are needed or not.
            Rule #6: There must be naming convention for each of the components
            Rule #7: You must review and adjust the overall recommendation for cohesion.
            Rule #8: This response will be used by another architect to create detailed plan. Keep the integration and cohesion in mind for this round.

            ** Important ** 
            Here's an example of a good response:
                Based on the analysis, here's the high-level requirement
                <response>
                    This application will be implemented using the following Cloud Services: API Gateway, Lambda, DynamoDB, S3, SSM, and SecurityGroup.
                    API Gateway:
                        - API Gateway 1:
                        - spec
                        - API Gateway 2:
                        - spec
                    Lambdas:
                        - Lambda 1:
                        - name:
                        - purpose:
                        - Lambda 2:
                        - name:
                        - purpose:
                    SSM parameters:
                        - Parameter 1:
                        - name:
                        - purpose:
                    DynamoDB:
                        - table 1
                        - purpose:
                        - name:
                </response>
        
            Example of a poor response:
                <response>
                    You can use AWS API Gateway, Azure API Gateway for endpoints. You can use Azure Functions, Containers, or AWS to run your application.
                    API Gateway
                    Lambdas: use lambda for compute
                    ssm parameters: use ssm parameters
                    DynamoDB: use dynamodb for storing data
                    S3 bucket: use s3 bucket to storing files
                </response>

            Now, think step by step on how the given functional requirements should be implemented. Create a cohesive and integrated Cloud Architecture to implement the services. Review your recommendation at least 3 times to ensure integrated plan.
        '''
    }
]

project_structure_rules = [
    '''
    Extract the lambda functions to be created in this format for each Lambda function.
    You must follow this rule:
    Rule #1: You must give each lambda function as separate element encapsulated in <response></response>

    ** Important **
    Here's an example of bad response
    <response>
        lambda 1
        lambda 2
        lambda 3
    </response>

    Here's an example of a good response
    Based on the analysis, here's the break-down
    <response>
        name:
        description:
        constraints:
    </response>
    <response>
        name:
        description:
        constraints:
    </response>
    '''
]