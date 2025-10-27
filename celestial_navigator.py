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
import json
import uuid

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import aiohttp

try:
    import pygame
except ImportError:
    print("Pygame is not installed. Please install it with 'pip install pygame'")
    exit(1)

# --- Configuration Section ---
baseConfig = configparser.ConfigParser()
SQLsettings = None
WEBHOOK_URL = None
sp = None

try:
    if os.name == 'nt':
        config_path = "C:\\SprocketBot\\configuration.ini"
    else:
        config_path = os.path.join(os.path.expanduser("~"), "configuration.ini")

    baseConfig.read(config_path)

    SQLsettings = baseConfig["SECURITY"]
    WEBHOOK_URL = baseConfig['settings']['bot_status_webhook']

    client_id = baseConfig['settings']['spotify_client_id']
    client_secret = baseConfig['settings']['spotify_client_secret']
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
except Exception as e:
    print(f"[Navigator] Could not read configuration. Exiting. Error: {e}")
    exit(1)

CONSTELLATION_PATH = "./celestial_audio/"


class CelestialNavigator:
    def __init__(self, pool):
        self.pool = pool
        self.ephemeris = []
        self.trajectory = []
        self.star_cluster_counter = 0
        self.nova_event_counter = 0
        self.pulsar_interval = random.randint(9, 11)
        self.nova_interval = random.randint(16, 19)
        self.running = True
        self.interrupt_flag = False
        self.snapshot_path = os.path.join(tempfile.gettempdir(), "celestial_trajectory.json")
        pygame.init()
        pygame.mixer.init()
        print("[Player] Audio systems initialized.")

    async def post_status(self, message):
        """Posts a status message to the webhook."""
        print(f"[Player] {message}")  # Also print to console
        if not WEBHOOK_URL: return
        async with aiohttp.ClientSession() as s: await s.post(WEBHOOK_URL,
                                                              json={'content': f"```[Player] {message}```"})

    def _update_trajectory_snapshot(self):
        try:
            snapshot_data = [{"designation": i.get("designation", "U"), "classification": i.get("classification", "U")}
                             for i in self.trajectory[:10]]
            with open(self.snapshot_path, 'w') as f:
                json.dump(snapshot_data, f)
        except Exception as e:
            print(f"Error writing trajectory snapshot: {e}")

    async def fetch_ephemeris(self):
        print("[Player] Fetching new ephemeris data...")
        today_column = f"{datetime.datetime.now().strftime('%a').lower()}_arc"
        async with self.pool.acquire() as connection:
            self.ephemeris = [dict(row) for row in
                              await connection.fetch(f"SELECT * FROM astral_bodies WHERE {today_column} = TRUE;")]
        print(f"[Player] Found {len(self.ephemeris)} valid bodies for today.")
        self.construct_trajectory()

    def construct_trajectory(self):
        print("[Player] Calculating new broadcast trajectory...")
        self.trajectory.clear()
        bodies = {k: [b for b in self.ephemeris if b['classification'] == k] for k in
                  ["STAR_CLUSTER", "NOVA_EVENT", "PULSAR_BURST"]}
        if not bodies["STAR_CLUSTER"]:
            print("[Player] Warning: No Star Clusters available.")
            self._update_trajectory_snapshot()
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
        print(f"[Player] Trajectory calculated with {len(self.trajectory)} events.")
        self._update_trajectory_snapshot()

    # MODIFIED: This function now performs a database search if the song is not in the daily cache.
    async def plot_priority_trajectory(self, unique_id: str):
        """Finds a body by ID and inserts it at the front of the queue."""
        print(f"[Player] Received priority request for body ID: {unique_id[:8]}...")

        # First, check the fast cache of daily songs
        priority_body = next((body for body in self.ephemeris if body['unique_id'] == unique_id), None)

        # If not in the cache, perform a direct database lookup (a "deep scan")
        if not priority_body:
            print(f"[Player] Cache miss for {unique_id[:8]}. Performing deep scan for unscheduled body...")
            try:
                async with self.pool.acquire() as connection:
                    record = await connection.fetchrow("SELECT * FROM astral_bodies WHERE unique_id = $1 LIMIT 1;",
                                                       unique_id)
                    if record:
                        priority_body = dict(record)
            except Exception as e:
                await self.post_status(f"ERROR: Database query failed during deep scan: {e}")
                return

        if priority_body:
            self.trajectory.insert(0, priority_body)
            await self.post_status(f"Success! '{priority_body['designation']}' is now next in the queue.")
            self._update_trajectory_snapshot()
        else:
            await self.post_status(
                f"Warning: Could not find priority body with ID {unique_id[:8]} in the entire catalog.")

    async def process_directives(self):
        while self.running:
            try:
                async with self.pool.acquire() as c:
                    directives = await c.fetch(
                        "SELECT * FROM celestial_directives WHERE processed = FALSE ORDER BY timestamp ASC;")
                    for d in directives:
                        print(f"[Player] Processing directive: {d['directive']}")
                        if d['directive'] == 'INTERRUPT':
                            self.interrupt_flag = True
                        elif d['directive'] == 'REALIGN':
                            self.running = False; self.interrupt_flag = True
                        elif d['directive'] == 'REFRESH_EPHEMERIS':
                            await self.fetch_ephemeris()
                        elif d['directive'] == 'PRIORITY_TRAJECTORY':
                            await self.plot_priority_trajectory(d['payload'])
                        await c.execute('UPDATE celestial_directives SET processed = TRUE WHERE id = $1;', d['id'])
            except Exception as e:
                print(f"Error processing directives: {e}")
            await asyncio.sleep(5)

    # ... (transmit, downloader functions, main, etc. are all unchanged from the last full version) ...
    async def transmit(self):
        print("[Player] Transmission commencing.")
        while self.running:
            if not self.trajectory:
                print("[Player] Trajectory empty. Recalculating...");
                self.construct_trajectory()
                if not self.trajectory:
                    print("[Player] No valid trajectory. Standing by.");
                    await asyncio.sleep(30);
                    continue
            self._update_trajectory_snapshot()
            current_body = self.trajectory.pop(0)
            filepath = current_body['filepath']
            if not os.path.exists(filepath):
                print(f"[Player] Warning: File not found for {current_body['designation']}. Skipping.");
                continue
            print(f"[Player] Transmitting: [{current_body['classification']}] {current_body['designation']}")
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.running:
                    if self.interrupt_flag:
                        pygame.mixer.music.stop();
                        self.interrupt_flag = False
                        print("[Player] Transmission interrupted.")
                        pulsars = [b for b in self.ephemeris if b['classification'] == 'PULSAR_BURST']
                        if pulsars: self.trajectory.insert(0, random.choice(pulsars))
                        self._update_trajectory_snapshot();
                        break
                    await asyncio.sleep(0.5)
            except pygame.error as e:
                print(f"[Player] Pygame error: {e}")
        pygame.mixer.quit();
        pygame.quit()
        print("[Player] Transmission ceased.")

    async def process_download_job(self, job):
        playlist_url = job['playlist_url'];
        day_bools = json.loads(job['day_bools_json']);
        requester_id = job['requester_id']
        await self.post_to_webhook(f"🚀 Starting bulk sync job for <{playlist_url}>")
        try:
            async with self.pool.acquire() as c:
                existing_designations = {r['designation'] for r in
                                         await c.fetch("SELECT LOWER(designation) as designation FROM astral_bodies")}
            tracks = [];
            results = sp.playlist_items(playlist_url)
            while results:
                tracks.extend(results['items']);
                results = sp.next(results) if results['next'] else None
            total = len(tracks)
            await self.post_to_webhook(f"Found **{total}** total tracks in the playlist.")
            s_count, sk_count = 0, 0
            for i, item in enumerate(tracks):
                if not item or not item['track']: continue
                track = item['track'];
                designation = f"{track['artists'][0]['name']} - {track['name']}"
                if designation.lower() in existing_designations: sk_count += 1; continue
                if (i + 1) % 5 == 0: await self.post_to_webhook(f"🛰️ Processing... ({i + 1}/{total})")
                try:
                    unique_id = str(uuid.uuid4());
                    search_query = f"{designation} lyrics"
                    ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [
                        {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                                'outtmpl': os.path.join(CONSTELLATION_PATH, f'{unique_id}.%(ext)s'),
                                'default_search': 'ytsearch1', 'quiet': True, 'noprogress': True}
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([search_query]))
                    filepath = os.path.join(CONSTELLATION_PATH, f'{unique_id}.mp3')
                    async with self.pool.acquire() as c:
                        await c.execute(
                            '''INSERT INTO astral_bodies (unique_id, designation, cataloger_id, classification, mon_arc, tue_arc, wed_arc, thu_arc, fri_arc, sat_arc, sun_arc, filepath) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);''',
                            unique_id, designation, requester_id, "STAR_CLUSTER", day_bools['mon_arc'],
                            day_bools['tue_arc'], day_bools['wed_arc'], day_bools['thu_arc'], day_bools['fri_arc'],
                            day_bools['sat_arc'], day_bools['sun_arc'], filepath)
                    existing_designations.add(designation.lower());
                    s_count += 1
                except Exception as e:
                    await self.post_status(f"ERROR ({i + 1}/{total}) Failed `{designation}`: `{type(e).__name__}`")
                await asyncio.sleep(1)
            await self.post_to_webhook(
                f"✨ **Sync Complete!** Cataloged **{s_count}** new bodies. Skipped **{sk_count}** duplicates.")
            await self.fetch_ephemeris()
        except Exception as e:
            await self.post_to_webhook(f"A critical error occurred during bulk sync: `{e}`")

    async def poll_download_queue(self):
        print("[Downloader] Waiting for new synchronization jobs...")
        while self.running:
            try:
                async with self.pool.acquire() as c:
                    job = await c.fetchrow(
                        "SELECT * FROM download_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
                    if job:
                        print(f"[Downloader] Found job {job['id']}. Processing.")
                        await c.execute("UPDATE download_queue SET status = 'processing' WHERE id = $1", job['id'])
                        await self.process_download_job(job)
                        await c.execute("UPDATE download_queue SET status = 'completed' WHERE id = $1", job['id'])
                        print(f"[Downloader] Finished job {job['id']}. Polling...")
            except Exception as e:
                print(f"[Downloader] Error in main loop: {e}")
            await asyncio.sleep(30)


async def main():
    pid = str(os.getpid());
    pidfile = os.path.join(tempfile.gettempdir(), "celestial_navigator.pid")
    if os.path.isfile(pidfile): print(f"{pidfile} exists. Is navigator running?"); return
    with open(pidfile, 'w') as f:
        f.write(pid)
    navigator_instance = None

    def shutdown_handler(signum, frame):
        if navigator_instance: navigator_instance.running = False; navigator_instance.interrupt_flag = True

    signal.signal(signal.SIGTERM, shutdown_handler);
    signal.signal(signal.SIGINT, shutdown_handler)
    try:
        pool = await asyncpg.create_pool(**SQLsettings, max_inactive_connection_lifetime=60)
        navigator_instance = CelestialNavigator(pool)
        await navigator_instance.fetch_ephemeris()
        directive_task = asyncio.create_task(navigator_instance.process_directives())
        downloader_task = asyncio.create_task(navigator_instance.poll_download_queue())
        player_task = asyncio.create_task(navigator_instance.transmit())
        await asyncio.gather(player_task, directive_task, downloader_task)
    finally:
        if os.path.exists(pidfile): os.unlink(pidfile)
        print("Navigator offline.")


if __name__ == "__main__":
    os.makedirs(CONSTELLATION_PATH, exist_ok=True)
    asyncio.run(main())