# celestial_navigator.py

import os
import asyncio
import asyncpg
import random
import time
import datetime
import configparser
import signal
import tempfile
import json  # ADDED

try:
    import pygame
except ImportError:
    print("Pygame is not installed. Please install it with 'pip install pygame'")
    exit(1)

# --- Configuration Section ---
# ... (This section is unchanged)
# celestial_navigator.py (Replacement for lines 26-34)

baseConfig = configparser.ConfigParser()
instanceConfig = configparser.ConfigParser()
try:
    if os.name == 'nt':  # This is Windows
        config_base_path = "C:\\SprocketBot\\"
        instance_name = "development.ini"
    else:  # This is for Linux/Raspberry Pi
        config_base_path = os.path.join(os.path.expanduser("~"), "")
        instance_name = "official.ini"

    baseConfig.read(os.path.join(config_base_path, "configuration.ini"))
    instanceConfig.read(os.path.join(config_base_path, "bots", instance_name))

    SQLsettings = baseConfig["SECURITY"]
    SQLsettings["database"] = instanceConfig["botinfo"]["sqldatabase"]
except Exception as e:
    print(f"Could not read configuration files. Ensure paths are correct. Error: {e}")
    exit(1)


class CelestialNavigator:
    def __init__(self, pool):
        # ... (This section is mostly unchanged)
        self.pool = pool
        self.ephemeris = []
        self.trajectory = []
        self.star_cluster_counter = 0
        self.nova_event_counter = 0
        self.pulsar_interval = random.randint(3, 5)
        self.nova_interval = random.randint(8, 12)
        self.running = True
        self.interrupt_flag = False

        # ADDED: Define the path for the queue snapshot
        self.snapshot_path = os.path.join(tempfile.gettempdir(), "celestial_trajectory.json")

        pygame.init()
        pygame.mixer.init()
        print("Audio systems initialized.")

    # ADDED: New function to write the queue state to a file
    def _update_trajectory_snapshot(self):
        """Saves the next 10 items of the queue to a JSON file for the bot to read."""
        try:
            snapshot_data = []
            # Take a slice of the next 10 items without modifying the actual queue
            for item in self.trajectory[:10]:
                snapshot_data.append({
                    "designation": item.get("designation", "Unknown"),
                    "classification": item.get("classification", "Unknown")
                })

            with open(self.snapshot_path, 'w') as f:
                json.dump(snapshot_data, f)
        except Exception as e:
            print(f"Error writing trajectory snapshot: {e}")

    async def fetch_ephemeris(self):
        # ... (This function is unchanged)
        print("Fetching new ephemeris data from the observatory log...")
        today_column = f"{datetime.datetime.now().strftime('%a').lower()}_arc"
        async with self.pool.acquire() as connection:
            query = f"SELECT * FROM astral_bodies WHERE {today_column} = TRUE;"
            self.ephemeris = [dict(row) for row in await connection.fetch(query)]
        print(f"Found {len(self.ephemeris)} valid celestial bodies for today.")
        self.construct_trajectory()

    def construct_trajectory(self):
        # ... (This function is mostly unchanged)
        print("Calculating new broadcast trajectory...")
        self.trajectory.clear()
        bodies = {
            "STAR_CLUSTER": [b for b in self.ephemeris if b['classification'] == 'STAR_CLUSTER'],
            "NOVA_EVENT": [b for b in self.ephemeris if b['classification'] == 'NOVA_EVENT'],
            "PULSAR_BURST": [b for b in self.ephemeris if b['classification'] == 'PULSAR_BURST']
        }
        if not bodies["STAR_CLUSTER"]:
            print("Warning: No Star Clusters (songs) available for broadcast.")
            self._update_trajectory_snapshot()  # ADDED: Update snapshot even if empty
            return
        random.shuffle(bodies["STAR_CLUSTER"])
        for cluster in bodies["STAR_CLUSTER"]:
            self.trajectory.append(cluster)
            self.star_cluster_counter += 1
            self.nova_event_counter += 1
            if self.star_cluster_counter >= self.pulsar_interval and bodies["PULSAR_BURST"]:
                self.trajectory.append(random.choice(bodies["PULSAR_BURST"]))
                self.star_cluster_counter = 0
                self.pulsar_interval = random.randint(3, 5)
            if self.nova_event_counter >= self.nova_interval and bodies["NOVA_EVENT"]:
                self.trajectory.append(random.choice(bodies["NOVA_EVENT"]))
                self.nova_event_counter = 0
                self.nova_interval = random.randint(8, 12)
        print(f"Trajectory calculated with {len(self.trajectory)} total events.")
        self._update_trajectory_snapshot()  # ADDED: Update snapshot after building

    async def plot_priority_trajectory(self, unique_id: str):
        # ... (This function is mostly unchanged)
        print(f"Plotting priority trajectory for body ID: {unique_id}")
        priority_body = next((body for body in self.ephemeris if body['unique_id'] == unique_id), None)
        if priority_body:
            self.trajectory.insert(0, priority_body)
            print(f"'{priority_body['designation']}' has been moved to the front of the trajectory.")
            self._update_trajectory_snapshot()  # ADDED: Update snapshot after modifying
        else:
            print(f"Warning: Could not find priority body with ID {unique_id} in current ephemeris cache.")

    async def process_directives(self):
        # ... (This function is unchanged)
        while self.running:
            try:
                async with self.pool.acquire() as connection:
                    directives = await connection.fetch('''
                        SELECT * FROM celestial_directives WHERE processed = FALSE ORDER BY timestamp ASC;
                    ''')
                    for d in directives:
                        print(f"Processing directive: {d['directive']}")
                        if d['directive'] == 'INTERRUPT':
                            self.interrupt_flag = True
                        elif d['directive'] == 'REALIGN':
                            self.running = False
                            self.interrupt_flag = True
                        elif d['directive'] == 'REFRESH_EPHEMERIS':
                            await self.fetch_ephemeris()
                        elif d['directive'] == 'PRIORITY_TRAJECTORY':
                            await self.plot_priority_trajectory(d['payload'])
                        await connection.execute('UPDATE celestial_directives SET processed = TRUE WHERE id = $1;',
                                                 d['id'])
            except Exception as e:
                print(f"Error processing directives: {e}")
            await asyncio.sleep(5)

    async def transmit(self):
        print("Transmission commencing.")
        while self.running:
            if not self.trajectory:
                print("Trajectory complete or empty. Recalculating...")
                self.construct_trajectory()
                if not self.trajectory:
                    print("No valid trajectory. Standing by for 30 seconds.")
                    await asyncio.sleep(30)
                    continue

            # MODIFIED: Update snapshot before popping the next item
            self._update_trajectory_snapshot()
            current_body = self.trajectory.pop(0)

            filepath = current_body['filepath']
            if not os.path.exists(filepath):
                print(f"Warning: File not found for {current_body['designation']}. Skipping.")
                continue
            print(f"Now transmitting: [{current_body['classification']}] {current_body['designation']}")
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.running:
                    if self.interrupt_flag:
                        pygame.mixer.music.stop()
                        self.interrupt_flag = False
                        print("Transmission interrupted by directive.")
                        pulsars = [b for b in self.ephemeris if b['classification'] == 'PULSAR_BURST']
                        if pulsars:
                            self.trajectory.insert(0, random.choice(pulsars))
                        self._update_trajectory_snapshot()  # ADDED: Update snapshot after interrupt
                        break
                    await asyncio.sleep(0.5)
            except pygame.error as e:
                print(f"Pygame error during playback of {filepath}: {e}")
        pygame.mixer.quit()
        pygame.quit()
        print("Celestial Navigator has ceased transmission.")


# ... (main function is unchanged)
async def main():
    pid = str(os.getpid())
    pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
    if os.path.isfile(pidfile):
        print(f"{pidfile} already exists. Is another navigator running?")
        return
    with open(pidfile, 'w') as f:
        f.write(pid)
    navigator_instance = None

    def shutdown_handler(signum, frame):
        print("Shutdown signal received. Cleaning up...")
        if navigator_instance:
            navigator_instance.running = False
            navigator_instance.interrupt_flag = True

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    try:
        pool = await asyncpg.create_pool(**SQLsettings)
        navigator_instance = CelestialNavigator(pool)
        await navigator_instance.fetch_ephemeris()
        directive_task = asyncio.create_task(navigator_instance.process_directives())
        await navigator_instance.transmit()
        directive_task.cancel()
        await pool.close()
    finally:
        if os.path.exists(pidfile):
            os.unlink(pidfile)
        print("PID file removed. Navigator offline.")


if __name__ == "__main__":
    asyncio.run(main())