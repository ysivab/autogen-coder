import argparse
import os
import shutil

class EnvPrep:
    def __init__(self):
        print("Env Prep")

    def confirm_action(self, prompt):
        """Utility function to prompt for user confirmation."""
        valid_responses = {"yes": True, "y": True, "no": False, "n": False}
        while True:
            choice = input(prompt).lower()
            if choice in valid_responses:
                return valid_responses[choice]
            else:
                print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

    def initiate(self, project_name, project_root) -> str:
        project_root_path = os.path.abspath(project_root)
        project_path = os.path.join(project_root_path, project_name)

        # Check if project_root starts with "/"
        if not project_root.startswith("/"):
            current_directory = os.getcwd()
            print(f"The project will be created under the current directory: {current_directory}")
            if not self.confirm_action("Do you want to proceed? (yes/no): "):
                exit()

        # Check if project_root exists and has project_name as a subdirectory
        if os.path.exists(project_root_path):
            if os.path.exists(project_path):
                delete_existing = self.confirm_action(f"The directory '{project_path}' already exists. Delete it? (yes/no): ")
                if delete_existing:
                    shutil.rmtree(project_path)
                    print(f"Deleted existing directory: {project_path}")
                else:
                    count = 1
                    new_project_path = f"{project_path}_{count}"
                    while os.path.exists(new_project_path):
                        count += 1
                        new_project_path = f"{project_path}_{count}"
                    project_path = new_project_path
                    print(f"Creating new directory: {project_path}")
        else:
            # Project root does not exist, confirm creation
            if self.confirm_action(f"The directory '{project_root_path}' does not exist. Create it? (yes/no): "):
                os.makedirs(project_root_path)
                print(f"Created directory: {project_root_path}")
            else:
                exit()

        # Create project_name as a subdirectory under project_root
        os.makedirs(project_path, exist_ok=True)

        return project_path
