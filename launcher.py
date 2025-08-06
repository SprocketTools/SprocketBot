import subprocess
import sys
import os
import time
import glob

def run_git_pull():
    """Runs the git pull command and prints the status."""
    print("Checking for updates from GitHub...")
    try:
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
    process = subprocess.Popen([sys.executable, 'main.py', config_name])
    return process

if __name__ == "__main__":
    run_git_pull()

    config_dir = "/home/mumblepi/bots/"
    config_files = glob.glob(os.path.join(config_dir, "*.ini"))

    if not config_files:
        print(f"No configuration files found in {config_dir}. Exiting.")
        sys.exit(1)

    processes = []
    for config_file in config_files:
        config_name = os.path.basename(config_file).replace('.ini', '')
        process = start_bot_instance(config_name)
        processes.append(process)

    print(f"Launched {len(processes)} bot instances. Launcher is now monitoring processes.")

    # Wait for all child processes to finish before exiting.
    # Since the bots are designed to run indefinitely, this will keep the launcher.py script,
    # and thus the systemd service, running.
    try:
        while True:
            # Check if all processes are still alive
            all_alive = all(p.poll() is None for p in processes)
            if not all_alive:
                # If any process has died, this is where you could add restart logic.
                # For now, we'll just wait.
                print("One or more bot processes have terminated.")
                # You might want to break here and let systemd handle the restart,
                # or add logic to restart the dead bot instance.
                # break
            time.sleep(10) # Wait for 10 seconds before checking again
    except KeyboardInterrupt:
        print("Launcher script terminated. Shutting down bot processes.")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()