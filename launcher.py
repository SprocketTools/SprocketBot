import subprocess
import sys
import os
import time
import glob
import signal
import platform
import tempfile


def is_process_running(pid: int) -> bool:
    """
    A cross-platform check to see if a process with a given PID is running.
    """
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, check=True
            )
            return str(pid) in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True


def launch_celestial_navigator():
    """
    Checks for and launches the independent music player process if not already running.
    This process is NOT monitored by the main loop and will persist through bot restarts.
    """
    pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
    python_executable = sys.executable
    command = [python_executable, 'celestial_navigator.py']

    if os.path.isfile(pidfile):
        try:
            with open(pidfile, 'r') as f:
                pid = int(f.read())

            if is_process_running(pid):
                print(f"--- Celestial Navigator is already running (PID: {pid}). ---")
                return
            else:
                print("--- Found stale PID file. Removing and starting navigator. ---")
                os.remove(pidfile)
        except (ValueError, FileNotFoundError):
            pass

    print("--- Launching Celestial Navigator process... ---")
    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

    subprocess.Popen(command, creationflags=creation_flags)
    time.sleep(2)


def run_update_and_pull():
    """
    Stashes local changes, pulls from GitHub, and returns True if successful.
    Disabled on Windows to simplify development.
    """
    if platform.system() != "Windows":
        print("--- Checking for updates from GitHub... ---")
        try:
            print("Stashing local changes (if any)...")
            stash_result = subprocess.run(
                ["git", "stash"], capture_output=True, text=True
            )
            if "No local changes to save" not in stash_result.stdout:
                print("Local changes were found and have been stashed.")

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
                "Your local changes may have been stashed. Use 'git stash list' and 'git stash pop' to recover them.")
            return False
    else:
        # On Windows, skip the git pull process.
        print("--- Skipping Git update check on Windows. ---")
        return True


def main_process_manager():
    """
    The main process manager loop that launches, monitors, and restarts bot instances.
    """
    if platform.system() == "Windows":
        config_dir = "C:\\SprocketBot\\bots\\"
    else:
        config_dir = "/home/mumblepi/bots/"

    config_files = glob.glob(os.path.join(config_dir, "*.ini"))

    if not config_files:
        print(f"No configuration files found in '{config_dir}'. Exiting.")
        return

    processes = {}
    python_executable = sys.executable

    for config_file in config_files:
        config_name = os.path.basename(config_file).replace('.ini', '')
        command = [python_executable, 'main.py', config_name]
        print(f"Starting instance '{config_name}'...")
        processes[config_name] = subprocess.Popen(command)
        time.sleep(3)

    print(f"--- Launched {len(processes)} bot instances. Monitoring... ---")

    while True:
        restart_needed = False
        for instance_name, process in processes.items():
            if process.poll() is not None:
                print(f"\n--- Instance '{instance_name}' has stopped (Exit Code: {process.poll()}). ---")
                print("--- Triggering a full system update and restart. ---")
                restart_needed = True
                break

        if restart_needed:
            for other_name, other_proc in processes.items():
                if other_proc.poll() is None:
                    print(f"Stopping instance '{other_name}' (PID: {other_proc.pid})...")
                    other_proc.terminate()

            for proc in processes.values():
                proc.wait()
            return
        time.sleep(10)


if __name__ == "__main__":
    # Launch the independent music player before starting the bot monitor.
    launch_celestial_navigator()

    try:
        while True:
            if not run_update_and_pull():
                print("--- Halting due to update failure. Please fix manually. ---")
                break
            main_process_manager()
            print("--- Restarting all bot services in 5 seconds... ---")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nLauncher received KeyboardInterrupt. Exiting.")
        pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
        if os.path.isfile(pidfile):
            try:
                with open(pidfile, 'r') as f:
                    pid = int(f.read())
                print(f"--- Sending shutdown signal to Celestial Navigator (PID: {pid}). ---")
                if platform.system() == "Windows":
                    os.kill(pid, signal.CTRL_C_EVENT)
                else:
                    os.kill(pid, signal.SIGTERM)
            except (OSError, ValueError):
                pass