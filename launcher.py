import subprocess
import sys
import os
import time
import glob


def run_update_and_pull():
    """
    Stashes local changes, pulls from GitHub, and returns True if successful.
    """
    print("--- Checking for updates from GitHub... ---")
    try:
        # Step 1: Stash any local changes to prevent pull conflicts.
        print("Stashing local changes (if any)...")
        stash_result = subprocess.run(
            ["git", "stash"], capture_output=True, text=True
        )
        if "No local changes to save" not in stash_result.stdout:
            print("Local changes were found and have been stashed.")

        # Step 2: Pull the latest code from the remote repository.
        print("Pulling latest code...")
        subprocess.run(
            ["git", "pull"], check=True, capture_output=True, text=True
        )

        print("--- Code is up to date. ---")
        return True

    except FileNotFoundError:
        print("ERROR: Git not found. Please install Git to use the auto-update feature.")
        return False
    except subprocess.CalledProcessError as e:
        print("--- ERROR: A Git command failed. Please check the logs below. ---")
        print(e.stdout)
        print(e.stderr)
        print(
            "Your local changes may have been stashed. Use 'git stash list' to check and 'git stash pop' to recover them after fixing the issue.")
        return False


def main_process_manager():
    """
    The main process manager loop that launches, monitors, and restarts bot instances.
    """
    # Discover all instances to run from the .ini files
    config_dir = "/home/mumblepi/bots/"
    config_files = glob.glob(os.path.join(config_dir, "*.ini"))

    if not config_files:
        print(f"No configuration files found in {config_dir}. Exiting.")
        return  # Exit the function, which will cause the script to stop.

    # Use a dictionary to map instance names to their process objects
    processes = {}
    python_executable = sys.executable

    # Launch all defined instances
    for config_file in config_files:
        config_name = os.path.basename(config_file).replace('.ini', '')
        command = [python_executable, 'main.py', config_name]
        print(f"Starting instance '{config_name}'...")
        processes[config_name] = subprocess.Popen(command)
        time.sleep(3)  # Stagger startups slightly

    print(f"--- Launched {len(processes)} bot instances. Monitoring... ---")

    # Monitoring loop
    while True:
        restart_needed = False
        for instance_name, process in processes.items():
            # poll() returns the exit code if the process has stopped, otherwise None.
            if process.poll() is not None:
                print(f"\n--- Instance '{instance_name}' has stopped (Exit Code: {process.poll()}). ---")
                print("--- Triggering a full system update and restart. ---")
                restart_needed = True
                break  # Exit the for-loop to begin shutdown

        if restart_needed:
            # Terminate all other running instances
            for other_name, other_proc in processes.items():
                if other_proc.poll() is None:
                    print(f"Stopping instance '{other_name}' (PID: {other_proc.pid})...")
                    other_proc.terminate()

            # Wait for all processes to fully close
            for proc in processes.values():
                proc.wait()

            return  # Exit this function to trigger a full restart cycle

        time.sleep(10)  # Check the status of processes every 10 seconds


if __name__ == "__main__":
    try:
        while True:
            # 1. Update the code with the new, more robust function
            if not run_update_and_pull():
                print("--- Halting due to update failure. Please fix manually. ---")
                break  # Exit the script completely if git fails

            # 2. Run the main monitoring loop
            main_process_manager()

            # 3. If main_process_manager returns, a restart is needed
            print("--- Restarting all services in 5 seconds... ---")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nLauncher received KeyboardInterrupt. Exiting.")
        # The main_process_manager isn't running, so no processes to kill here.
        # This will cleanly exit the script.