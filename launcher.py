# launcher.py
import subprocess
import sys
import os
import time

def run_git_pull():
    """Runs the git pull command and prints the status."""
    print("Checking for updates from GitHub...")
    try:
        # Run the command
        result = subprocess.run(
            ["git", "pull"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if "Already up to date." not in result.stdout:
            print("Update complete. Restarting in 3 seconds...")
            time.sleep(3)

    except FileNotFoundError:
        print("ERROR: Git not found. Skipping update.")
    except subprocess.CalledProcessError as e:
        print("ERROR: 'git pull' failed. Please resolve conflicts manually.")
        print(e.stderr)
        # We exit here to prevent running the bot with broken/conflicted code
        sys.exit(1)

def start_bot():
    """Starts the main bot process."""
    print("Starting main.py...")
    # os.execv replaces the current process (launcher.py) with the new one (main.py).
    # This is efficient and ensures the launcher doesn't keep running in the background.
    try:
        os.execv(sys.executable, ['python3'] + ['main.py'])
    except FileNotFoundError:
        print("ERROR: Could not find main.py. Make sure you are in the correct directory.")
        sys.exit(1)


if __name__ == "__main__":
    run_git_pull()
    start_bot()