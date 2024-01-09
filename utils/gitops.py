from git import Repo

def git_init(repo_path):
    try:
        repo = Repo.init(repo_path)
        print(f"Initialized a new git repository at {repo_path}")
        return repo
    except Exception as e:
        print(f"Failed to initialize Git repository: {e}")


def git_commit(repo, message):
    try:
        # Stage all changes
        repo.git.add(all=True)

        # Commit
        repo.index.commit(message)
        print(f"Committed changes with message: '{message}'")
    except Exception as e:
        print(f"Failed to commit changes: {e}")
