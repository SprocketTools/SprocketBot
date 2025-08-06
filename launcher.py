# launcher.py
import platform
import subprocess
import sys
import os
import time
import glob


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
        sys.exit(1)


def start_bot_instance(config_name):
    """Starts a single bot instance with a specified configuration."""
    print(f"Starting main.py for configuration: {config_name}...")
    # Use subprocess.Popen to run the bot instance as a separate process.
    # We pass the configuration name as a command-line argument.
    # The main.py script would need to be modified to accept this argument.
    process = subprocess.Popen([sys.executable, 'main.py', config_name])
    return process


if __name__ == "__main__":
    run_git_pull()

    # Define the directory where your configuration files are located
    if platform.system() == "Windows":
        config_dir = "C:\SprocketBot\\bots\\"
    else:
        config_dir = "/home/mumblepi/bots/"

    # Find all .ini files in the configuration directory
    config_files = glob.glob(os.path.join(config_dir, "*.ini"))

    if not config_files:
        print(f"No configuration files found in {config_dir}. Exiting.")
        sys.exit(1)

    processes = []
    for config_file in config_files:
        # Extract the configuration name from the filename (e.g., "official" from "official.ini")
        config_name = os.path.basename(config_file).replace('.ini', '')
        # Start a bot instance for each configuration
        process = start_bot_instance(config_name)
        processes.append(process)

    print(f"Launched {len(processes)} bot instances.")
    # You can add logic here to monitor the processes if needed
    # For example, using a loop to check if they are still running.