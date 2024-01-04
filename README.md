
# AutoGen-Coder

AutoGen-Coder is an innovative application based on the AutoGen framework by Microsoft, designed to streamline the software development life cycle (SDLC) through multi-agent conversations. This tool automates the process of generating code and deployment templates from requirement or architecture documents.

## Features

- **Multi-Agent Conversation**: Engages users in a conversational manner, involving expert and critic personas at each stage of the SDLC.
- **Comprehensive SDLC Stages**: Includes Plan, Design, Develop, Integrate, and Deploy stages, each equipped with specific roles and functions.
- **Automated Code and Template Generation**: Transforms requirement and architecture documents into executable code and deployment templates.

## Installation

1. To install dependencies, run the following command:

```bash
pip install -r requirements.txt
```

2. Create "notebook" directory
3. Create a file OAI_CONFIG_LIST (you can add additional models as required)
```
[
  {
    "model": "gpt-3.5-turbo",
    "api_key": "<KEY>"
  },
  {
    "model": "gpt-3.5-turbo-16k",
    "api_key": "<KEY>"
  }
]
```
3. In each SDLC/*.py file can modify 

```
self.config_list = autogen.config_list_from_json(
    "notebook/OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-3.5-turbo-16k"]
    },
)
```
4. Setup your AWS access


## Usage

AutoGen-Coder is operated through a series of commands, corresponding to different stages of the SDLC:

1. **Plan and Design Phase**:
   - Engages Chief Product Officer and Product Manager for the Plan phase.
   - Involves Chief Technology Officer and Software Architect for the Design phase.
   
   ```bash
   main.py --config awslambda --project-root /path/to/dir --project-name name --task "develop a simple HelloWorld API"
   ```

   ```bash
   main.py --config awslambda --project-root /path/to/dir --project-name name --requirement-doc /path/to/word.docx
   ```

2. **Direct Architecture Implementation**:
   - This command expects a technical document and details the resources to be deployed.
   - Skips the Plan and Design stages.

   ```bash
   main.py --config awslambda --project-root /path/to/dir --project-name name --architecture-doc /path/to/architecture.md
   ```

