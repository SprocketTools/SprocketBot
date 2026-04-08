import asyncio
import copy
import json
import math
import discord
import numpy
from PIL import Image
from discord.ext import commands
import random
import io
from datetime import datetime
import numpy as np
import matplotlib

matplotlib.use('Agg')
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class blueprintAnalysisTools:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _render_worker(vertices, faces, iframes=12):
        """
        Optimized 3D rendering:
        - Reuses the Figure/Axes objects (avoids teardown/setup overhead).
        - Uses raw buffer access (avoids PNG encoding/decoding).
        - Manual margin adjustment (avoids costly bbox_inches calculation).
        """
        try:
            # 1. Coordinate Transformations (Same as before)
            vertices = vertices[:, [0, 2, 1]]

            # 2. Calculate Scene Bounds (Same as before)
            x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
            y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
            z_min, z_max = vertices[:, 2].min(), vertices[:, 2].max()

            center = np.array([
                np.mean([x_min, x_max]),
                np.mean([y_min, y_max]),
                np.mean([z_min, z_max])
            ])

            max_range = np.array([
                x_max - x_min,
                y_max - y_min,
                z_max - z_min
            ]).max() / 3.0 * 1.1

            polygons = [vertices[face['v']] for face in faces]

            # --- SETUP PHASE (Done ONCE) ---
            # Set DPI lower if you want even more speed (e.g., 100 or 120)
            fig = plt.figure(figsize=(8, 8), dpi=120)
            ax = fig.add_subplot(111, projection='3d')

            # Manual Layout: Removes whitespace without the slow 'bbox_inches="tight"'
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

            # Styling
            bg_color = (0.05, 0.05, 0.1)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            ax.axis('off')

            # Add Geometry ONCE
            mesh_collection = Poly3DCollection(
                polygons,
                edgecolors=(0.8, 1.0, 1.0),
                facecolors=(0.1, 0.2, 0.3, 0.5),
                linewidths=0.5
            )
            ax.add_collection3d(mesh_collection)

            # Set Limits ONCE
            ax.set_xlim(center[0] - max_range, center[0] + max_range)
            ax.set_ylim(center[1] - max_range, center[1] + max_range)
            ax.set_zlim(center[2] - max_range, center[2] + max_range)
            ax.set_box_aspect([1, 1, 1])
            ax.dist = 8.5

            images = []

            # --- RENDER LOOP (Fast) ---
            for i in range(iframes):
                # 1. Rotate Camera
                azim = (360 / iframes) * i + (180 / iframes)
                elev = 15
                ax.view_init(elev=elev, azim=azim)

                # 2. Draw to Canvas
                fig.canvas.draw()

                # 3. Direct Buffer Access (Fastest Method)
                # buffer_rgba returns an RGBA buffer directly, no swapping needed.
                # Image.frombuffer is faster than frombytes as it avoids data copying.
                w, h = fig.canvas.get_width_height()
                buf = fig.canvas.buffer_rgba()

                image = Image.frombytes("RGBA", (w, h), buf, "raw", "RGBA")
                images.append(image)

            # Cleanup
            plt.close(fig)

            if not images:
                return None

            # 4. Compile GIF
            gif_buffer = io.BytesIO()
            images[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=images[1:],
                duration=3500 / iframes,
                loop=0
            )
            gif_buffer.seek(0)
            return gif_buffer

        except Exception as e:
            print(f"Render worker failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    # --- HELPER: Async Interface ---
    async def generate_blueprint_gif(self, mesh_data, name, iframes=12):
        """
        Async helper to generate a 3D GIF.
        Call this from other commands (like analyzeBlueprint).
        """
        vertices_list = mesh_data["vertices"]
        face_list = mesh_data["faces"]

        if not vertices_list:
            return None

        # Convert to numpy array before passing to thread
        vertices = numpy.array(vertices_list).reshape(-1, 3)

        # Offload the blocking render_worker to a thread
        gif_buffer = await asyncio.to_thread(
            self._render_worker,
            vertices,
            face_list,
            iframes
        )

        if gif_buffer:
            return discord.File(gif_buffer, filename=f'{name}_render.gif')
        return None

    def runMeshMirror(self, meshData, sourcePartInfo):
        sourcePartPosX = sourcePartInfo["pos"][0]
        sourcePartPosY = sourcePartInfo["pos"][1]
        sourcePartPosZ = sourcePartInfo["pos"][2]
        sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
        sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
        sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
        sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
        sourcePartPointsLength = len(sourcePartPoints)

        pos = 0
        # vector rotation
        while pos < sourcePartPointsLength:
            sourcePartPoints[pos] = -1 * (sourcePartPoints[pos])
            pos += 3
        return sourcePartPoints

    def _get_face_normal(self, v1, v2, v3):
        """Calculates the normal vector of a face defined by three vertices."""
        vec1 = np.array(v2) - np.array(v1)
        vec2 = np.array(v3) - np.array(v1)
        normal = np.cross(vec1, vec2)
        # Normalize the vector
        norm_len = np.linalg.norm(normal)
        if norm_len == 0:
            return None  # Avoid division by zero for degenerate faces
        return normal / norm_len

    def _calculate_cannon_stats(self, caliber_mm, prop_len_mm, barrel_len_mm, k_val, psi, proj_len_mm):

        # 2. TRAVEL CALCULATION (The 'Anomaly Fix')
        # Bullet Travel is the distance from the end of the case to the muzzle.
        bullet_travel_mm = barrel_len_mm + (caliber_mm*3)

        print("STATS: ", caliber_mm, prop_len_mm, barrel_len_mm, k_val, psi, proj_len_mm)

        if caliber_mm <= 0 or prop_len_mm <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0

        # --- FIX: Fallback for missing/zero projectile length ---
        #if not proj_len_mm or proj_len_mm <= 0:
        shell_len_mm = caliber_mm * 3.0
        #else:
            #shell_len_mm = proj_len_mm

        # 1. Internal Constants
        LENGTH_CONV = 1 / 25.4
        MAX_ER = 50.0
        PROJ_DENSITY = 7000.0
        LOAD_DENSITY = 0.97

        # 2. Geometry & Unit Alignment
        case_mm = prop_len_mm

        # Blueprint barrel segments act as the pure travel distance
        bullet_travel_in = barrel_len_mm * LENGTH_CONV
        total_length_m = (barrel_len_mm + prop_len_mm + shell_len_mm) / 1000.0

        if bullet_travel_in <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0, total_length_m, 1.0

        # 3. Volume and Expansion Ratio (Imperial Path)
        proj_len_mm = caliber_mm * 3.0

        # 4. VOLUME & EXPANSION
        area_m2 = np.pi * np.power(caliber_mm / 2000.0, 2.0)
        case_vol_grains = (case_mm * 0.001 * area_m2 * 1000.0) * 15432.0

        net_capacity_water = case_vol_grains / 252.4
        area_bore_in = 0.773 * np.power(caliber_mm * LENGTH_CONV, 2.0)
        bore_vol_in = (bullet_travel_mm * LENGTH_CONV) * area_bore_in

        er_raw = (bore_vol_in + net_capacity_water) / net_capacity_water
        er = np.minimum(er_raw, MAX_ER)

        print(er)
        # 4. Mass Balance
        powder_weight_grains = LOAD_DENSITY * case_vol_grains
        propellant_mass_kg = powder_weight_grains / 15432.4

        proj_vol_m3 = (shell_len_mm / 1000.0) * area_m2
        proj_mass_kg = proj_vol_m3 * PROJ_DENSITY
        proj_weight_grains = proj_mass_kg * 15432.4

        # Secondary safety catch
        if proj_weight_grains <= 0:
            return 0.0, 0.0, 0.0, 0.0, propellant_mass_kg, total_length_m, er

        a = powder_weight_grains / proj_weight_grains

        # 5. Pressure & Powley Polynomials
        operating_pressure = (psi + 17902) / 1.516

        mf2_poly = (1.071 + er - 0.009736 * math.pow(er, 2.0))
        mf2 = 0.024075 * (9.3 - a) * mf2_poly
        k = 0.53 / a + 0.26

        # Check for unphysical mass ratio (a >= 9.3) causing math collapse
        if mf2 <= 0 or k <= 0 or a >= 9.3:
            return 0.0, 0.0, 0.0, proj_mass_kg, propellant_mass_kg, total_length_m, er

        # 6. Final Velocity Calculation (FPS -> M/S)
        v_man_sq = (operating_pressure / k / mf2 * (er - 1) / 0.86 / 134.7)
        v_man = 100 * math.sqrt(max(0, v_man_sq))
        muzzle_velocity = v_man / 3.28084

        # 7. Energy and Penetration (Tuned Krupp/DeMarre Formula)
        ke_mj = (0.5 * proj_mass_kg * math.pow(muzzle_velocity, 2)) / 1_000_000.0

        caliber_dm = caliber_mm / 100.0
        penetration_mm = 0.0

        if k_val > 0 and caliber_dm > 0:
            # --- Exactly Tuned Exponents from Game Data ---
            EXP_V = 1.0250
            EXP_M = 0.4384
            EXP_D = 0.5485
            EXP_MASTER = 1.3979

            # Equation: base = (V^exp_v * M^exp_m) / (K * D^exp_d)
            pen_dm_base = (math.pow(muzzle_velocity, EXP_V) * math.pow(proj_mass_kg, EXP_M)) / (
                        k_val * math.pow(caliber_dm, EXP_D))

            # Final calculation
            pen_dm = math.pow(pen_dm_base, EXP_MASTER)
            penetration_mm = pen_dm * 100.0

        return (
            round(muzzle_velocity, 2),
            round(ke_mj, 2),
            round(penetration_mm, 2),
            round(proj_mass_kg, 2),
            round(propellant_mass_kg, 2),
            round(total_length_m, 2),
            round(er, 2)
        )

    def _get_barrel_length(self, segments):
        """Recursively parses barrel segment dictionaries to find total barrel length"""
        length = 0
        if isinstance(segments, list):
            for seg in segments:
                length += self._get_barrel_length(seg)
        elif isinstance(segments, dict):
            if 'l' in segments:
                length += segments['l']
            if 'segments' in segments:
                length += self._get_barrel_length(segments['segments'])
        return length

    async def _parse_blueprint_stats(self, ctx: commands.Context, blueprint_data: dict) -> dict:
        """
        Parses the blueprint dictionary and extracts specified vehicle statistics.
        """
        try:
            stats = {}

            # --- Placeholders ---
            stats["vehicle_class"] = "Placeholder"
            stats["host_id"] = 0
            stats["faction_id"] = 0
            stats["base_cost"] = 1000
            stats["ground_pressure"] = 0.0
            stats["travel_range"] = 0
            stats["upper_frontal_angle"] = 0.0
            stats["lower_frontal_angle"] = 0.0
            stats["health"] = 0
            stats["attack"] = 0
            stats["defense"] = 0
            stats["breakthrough"] = 0
            stats["piercing"] = 0
            stats["armor"] = 0
            stats["cohesion"] = 0
            stats["upper_frontal_angle"] = 0.0
            stats["lower_frontal_angle"] = 0.0
            stats["health"] = 0
            stats["attack"] = 0
            stats["defense"] = 0
            stats["breakthrough"] = 0
            stats["piercing"] = 0
            stats["armor"] = 0
            stats["cohesion"] = 0

            # --- Real Data ---
            stats["vehicle_id"] = random.randint(1_000_000_000, 9_999_999_999)  # Random 10-digit ID
            stats["owner_id"] = ctx.author.id

            # 1. Tank Weight
            stats["tank_weight"] = blueprint_data["header"]["mass"]
            stats["base_cost"] = blueprint_data["header"]["cost"]
            tank_weight_tons = stats["tank_weight"] / 1000.0

            # 2. Crew Count
            crew_count = 0
            for bp in blueprint_data.get("blueprints", []):
                if bp.get("type") == "crewSeat":
                    crew_count += 1
            stats["crew_count"] = crew_count

            # --- Pre-cache data for efficiency ---
            blueprints = {bp['id']: {'type': bp['type'], 'bp': bp.get('blueprint', {})} for bp in
                          blueprint_data.get('blueprints', [])}
            meshes = {mesh['vuid']: mesh for mesh in blueprint_data.get('meshes', [])}
            objects_by_vuid = {obj['vuid']: obj for obj in blueprint_data.get('objects', [])}
            turret_ring_bp_vuids = {bp['id'] for bp in blueprint_data.get('blueprints', []) if
                                    bp['type'] == 'turretRing'}

            # Cache base dimensions of fuel tanks
            fuel_tank_blueprints = {}
            for bp_id, bp_data in blueprints.items():
                if bp_data['type'] == 'fuelTank':
                    bp = bp_data['bp']
                    fuel_tank_blueprints[bp_id] = {'x': bp.get('x', 0), 'y': bp.get('y', 0), 'z': bp.get('z', 0)}

            # Cache wheel diameters
            wheel_diameters_m = {bp['id']: bp['blueprint']['diameter'] for bp in blueprint_data['blueprints'] if
                                 bp['type'] == 'trackWheel'}

            # 3. Tank Length & Hull Width
            hull_min_x, hull_max_x = math.inf, -math.inf
            hull_min_z, hull_max_z = math.inf, -math.inf
            max_hull_y = -math.inf
            hull_width = 0.0
            stats["tank_length"] = 0.0

            all_vertices = {}  # Store all mesh vertices for angle calcs
            hull_mesh = meshes.get(0)  # Hull mesh is always vuid 0

            if hull_mesh:
                vertices_list = hull_mesh.get("meshData", {}).get("mesh", {}).get("vertices", [])
                # Convert flat list to list of [x, y, z] coords
                v_coords = []
                if vertices_list:
                    i = 0
                    while i < len(vertices_list):
                        x = vertices_list[i]
                        y = vertices_list[i + 1]
                        z = vertices_list[i + 2]
                        v_coords.append([x, y, z])

                        if x < hull_min_x: hull_min_x = x
                        if x > hull_max_x: hull_max_x = x
                        if y > max_hull_y: max_hull_y = y  # Get hull top
                        if z < hull_min_z: hull_min_z = z
                        if z > hull_max_z: hull_max_z = z
                        i += 3

                    all_vertices[0] = v_coords  # Store hull vertices
                    stats["tank_length"] = (hull_max_z - hull_min_z)
                    hull_width = (hull_max_x - hull_min_x)

            # 4. Tank Width (Max of Hull vs Tracks)
            track_sep_m = 0.0
            track_width_m = 0.0
            total_track_width = 0.0
            chassis_ground_clearance_mm = 0

            # --- 5. Powertrain, Era, Chassis, & Cannons info ---
            cylinder_count = 2  # Default
            cylinder_displacement = 1.0  # Default
            total_armor_volume = 0.0
            cannons_info = []
            max_pen = 0.0
            max_mv = 0.0
            total_ke_mj = 0.0

            # Additional trackers for database validation
            best_proj_mass = 0.0
            best_prop_mass = 0.0
            best_gun_len = 0.0
            best_er = 0.0
            best_caliber = 0.0
            best_prop_len = 0.0
            best_bore_len = 0.0

            vehicle_era = blueprint_data["header"].get("era", "Latewar")

            # Era-specific values from TopGearCalculator.html
            era_params = {
                "WWI": {"R": 4, "eraPowerMod": 0.2333},
                "Interwar": {"R": 3, "eraPowerMod": 0.586},
                "Earlywar": {"R": 1.5, "eraPowerMod": 0.72},
                "Midwar": {"R": 1.25, "eraPowerMod": 0.92},
                "Latewar": {"R": 1.0, "eraPowerMod": 1.00}
            }

            # Check for creationDate if era is not present
            if "era" not in blueprint_data["header"]:
                era_start_dates = [
                    (datetime.strptime("1944.01.01", "%Y.%m.%d").date(), "Latewar"),
                    (datetime.strptime("1942.01.01", "%Y.%m.%d").date(), "Midwar"),
                    (datetime.strptime("1939.09.02", "%Y.%m.%d").date(), "Earlywar"),
                    (datetime.strptime("1918.11.12", "%Y.%m.%d").date(), "Interwar"),
                    (datetime.strptime("1914.07.28", "%Y.%m.%d").date(), "WWI")
                ]
                vehicle_date_str = blueprint_data["header"].get("creationDate")
                if vehicle_date_str:
                    try:
                        vehicle_date_obj = datetime.strptime(vehicle_date_str, "%Y.%m.%d").date()
                        for era_date, era_name in era_start_dates:
                            if vehicle_date_obj >= era_date:
                                vehicle_era = era_name
                                break  # Found the latest era
                    except ValueError:
                        pass  # Default to Latewar

            stats["vehicle_era"] = vehicle_era

            era_data = era_params.get(vehicle_era, era_params["Latewar"])  # Default to Latewar
            R_val = era_data["R"]
            era_power_mod = era_data["eraPowerMod"]

            for bp_id, bp_data in blueprints.items():
                bp_type = bp_data['type']
                bp = bp_data['bp']

                # Capture Cannons Data dynamically
                if bp_type == 'cannon':
                    cal = bp.get('caliber', 0)
                    k_val = bp.get('K', 2400)
                    psi_val = bp.get('PSI', 25000)
                    b_len = self._get_barrel_length(bp.get('segments', []))

                    # Link to the specific Ammunition (shellSlot)
                    shell_id = bp.get('shellID')
                    prop_len = bp.get('breechLength', 0)
                    proj_len = cal * 3.0  # Fallback

                    if shell_id is not None and shell_id in blueprints:
                        shell_data = blueprints[shell_id]['bp']
                        # shellSlot stores length directly
                        prop_len = shell_data.get('propellantLength', prop_len)

                        # Check for specific projectile overrides in generatedProjectiles
                        gen_projs = shell_data.get('generatedProjectiles', [])
                        if gen_projs:
                            first_proj = gen_projs[0]
                            for func in first_proj.get('functions', []):
                                f_id = func.get('id')
                                f_def = func.get('definition', {})
                                if f_id == 'AP':
                                    k_val = f_def.get('penetratorConstant', k_val)
                                elif f_id == 'Propellant':
                                    # Some versions store prop length here
                                    prop_len = f_def.get('length', prop_len)

                    vel, ke, pen, proj_mass, prop_mass, bore, er = self._calculate_cannon_stats(cal, prop_len, b_len,
                                                                                                k_val, psi_val,
                                                                                                proj_len)

                    if cal > 0:
                        essential_str = (
                            f"**{int(cal)}x{int(prop_len)}mm Cannon\n**"
                            f"{vel:.0f} m/s | {ke:.1f} MJ KE | {pen:.0f}mm pen"
                        )
                        cannons_info.append(essential_str)

                        total_ke_mj += ke
                        if pen > max_pen:
                            max_pen = pen
                            max_mv = vel
                            best_proj_mass = proj_mass
                            best_prop_mass = prop_mass
                            best_gun_len = bore
                            best_er = er
                            best_caliber = cal
                            best_prop_len = prop_len
                            best_bore_len = b_len / 1000.0

                if bp_type == "track":
                    track_sep_m = bp.get("separation", 0) / 1000.0
                if bp_type == "trackBelt":
                    track_width_m = bp.get("x", 0) / 1000.0
                if bp_type == "chassis":
                    chassis_ground_clearance_mm = bp.get("groundClearance", 0)
                if bp_type == "engine":
                    cylinder_count = bp.get("cylinders", 2)
                    cylinder_displacement = bp.get("cylinderDisplacement", 1.0)
                if bp_type == "structure":
                    total_armor_volume += bp.get("armourVolume", 0.0)

                    # Cache vertices for any structure mesh
                    mesh_vuid = bp.get("bodyMeshVuid")
                    if mesh_vuid not in all_vertices and mesh_vuid in meshes:
                        mesh = meshes[mesh_vuid]
                        vertices_list = mesh.get("meshData", {}).get("mesh", {}).get("vertices", [])
                        v_coords = []
                        if vertices_list:
                            i = 0
                            while i < len(vertices_list):
                                v_coords.append([vertices_list[i], vertices_list[i + 1], vertices_list[i + 2]])
                                i += 3
                            all_vertices[mesh_vuid] = v_coords

            # Finalize Cannon String
            if cannons_info:
                stats["cannon_stats"] = "\n\n".join(cannons_info)[:1000]  # Ensure it fits in db
            else:
                stats["cannon_stats"] = "None"

            stats["muzzle_velocity"] = max_mv
            stats["penetration"] = max_pen
            stats["ke_mj"] = total_ke_mj
            stats["proj_mass"] = best_proj_mass
            stats["prop_mass"] = best_prop_mass
            stats["gun_len"] = best_gun_len
            stats["er"] = best_er
            stats["caliber"] = best_caliber
            stats["prop_len"] = best_prop_len
            stats["bore_len"] = best_bore_len

            stats["armor_mass"] = total_armor_volume * 7850  # Convert m^3 of steel to kg

            if track_sep_m > 0 and track_width_m > 0:
                total_track_width = track_sep_m + (2 * track_width_m)

            stats["tank_width"] = max(hull_width, total_track_width)

            # 6. Tank Height

            # 6a. Find lowest point (bottom of roadwheels)
            lowest_point_y = math.inf

            for bp in blueprint_data.get('blueprints', []):
                if bp.get('type') == 'trackWheelArray':
                    array_bp = bp.get('blueprint', {})
                    y_offset_m = array_bp.get('yOffset', 0) / 1000.0
                    wheel_vuid = array_bp.get('sharedWheelBlueprintVuid')  # This is the *wheel* ID

                    if wheel_vuid in wheel_diameters_m:
                        diameter = wheel_diameters_m[wheel_vuid]
                        radius = diameter / 2.0
                        wheel_bottom_y = y_offset_m - radius
                        lowest_point_y = min(lowest_point_y, wheel_bottom_y)

            # 6b. Find highest point (hull or turret)
            max_vehicle_y = max_hull_y

            for obj in blueprint_data.get('objects', []):
                if obj.get('ringBlueprintVuid') in turret_ring_bp_vuids:
                    try:
                        # Height of the turret ring itself
                        ring_y = obj['transform']['pos'][1]

                        # Find the structure object attached to the ring
                        structure_vuid = obj.get('structureID')
                        if not structure_vuid: continue
                        structure_obj = objects_by_vuid.get(structure_vuid)
                        if not structure_obj: continue

                        # Get that structure's offset from the ring
                        structure_offset_y = structure_obj['transform']['pos'][1]

                        # Get that structure's blueprint to find its mesh
                        structure_bp_vuid = structure_obj.get('structureBlueprintVuid')
                        structure_bp_data = blueprints.get(structure_bp_vuid)  # Use pre-cached dict
                        if not structure_bp_data: continue

                        # Get the mesh vuid
                        mesh_vuid = structure_bp_data['bp'].get('bodyMeshVuid')
                        if mesh_vuid not in all_vertices: continue  # Skip if mesh not cached

                        v_coords = all_vertices[mesh_vuid]

                        # Find the highest vertex *within that mesh*
                        max_mesh_y = -math.inf
                        if v_coords:
                            for v in v_coords:
                                max_mesh_y = max(max_mesh_y, v[1])  # v[1] is 'y'
                        else:
                            max_mesh_y = 0

                        # Total turret height = ring base + structure offset + highest point on mesh
                        total_turret_top_y = ring_y + structure_offset_y + max_mesh_y

                        # Check if this is the new highest point
                        max_vehicle_y = max(max_vehicle_y, total_turret_top_y)
                    except Exception:
                        # Ignore errors on this turret and continue
                        pass

            # 6c. Calculate Physical Height (bottom of wheel to top of vehicle)
            if lowest_point_y == math.inf:  # Failsafe if no tracks found
                lowest_point_y = 0

            stats["tank_height"] = max_vehicle_y - lowest_point_y

            # 6d. Calculate Total Height (from ground plane to top of vehicle)
            ground_clearance_m = chassis_ground_clearance_mm / 1000.0
            stats["tank_total_height"] = max_vehicle_y + ground_clearance_m

            # 7. Powertrain Calculations (HP, HP/T, Top Speed)
            try:
                H = cylinder_count * 40 * era_power_mod * (cylinder_displacement ** 0.7)
                stats["horsepower"] = int(H)

                W = tank_weight_tons
                stats["hpt"] = H / W

                TopSpeed = (13.666 * (H ** 0.501)) / ((R_val ** 0.8) * (W ** 0.5))
                stats["top_speed"] = int(TopSpeed)
            except Exception:
                # Failsafe in case of math error
                stats["horsepower"] = 0
                stats["hpt"] = 0.0
                stats["top_speed"] = 0

            # 8. Ground Pressure
            ground_pressure = 0.0
            contact_length_m = 0.0
            belt_width_m = track_width_m  # from section 5
            wheelDiameter = 0.0
            best_array_bp = None
            roadwheel_diameter_m = -1.0

            # --- Extract Suspension Type & Scale via GUIDs ---
            suspension_type = "torsionBar"
            suspension_scale = 1.0

            for bp_entry in blueprint_data.get('blueprints', []):
                bp_type = bp_entry.get('type', '')
                bp_data = bp_entry.get('blueprint', {})

                if bp_type == 'trackWheelMount':
                    mount_id = bp_data.get('mountID', '')
                    if mount_id == 'b84298aa-f287-4752-aca5-fa2b78ce4f02':  # HVSS
                        suspension_type = 'HVSS'
                        suspension_scale = bp_data.get('scale', 1.0)
                    elif mount_id == 'c9314baa-f287-4752-aca5-fa2b78ce4f02':  # VVSS
                        suspension_type = 'VVSS'
                        suspension_scale = bp_data.get('scale', 1.0)
                    elif mount_id == 'a5d242f0-ab76-4f51-b8c0-5ffd795c9130':  # Leaf Spring
                        suspension_type = 'leafSpring'
                        suspension_scale = bp_data.get('scale', 1.0)
            # ---------------------------------------------

            # Find all wheel array *objects*
            for obj in blueprint_data.get('objects', []):
                if "wheelMountArrayBlueprintVuid" in obj and "sharedWheelBlueprintVuid" in obj:
                    array_bp_id = obj.get('wheelMountArrayBlueprintVuid')
                    wheel_bp_id = obj.get('sharedWheelBlueprintVuid')

                    if wheel_bp_id in wheel_diameters_m:
                        current_diameter_m = wheel_diameters_m[wheel_bp_id]

                        # We only want roadwheels, not return rollers
                        if current_diameter_m > roadwheel_diameter_m:
                            roadwheel_diameter_m = current_diameter_m
                            best_array_bp = blueprints.get(array_bp_id, {}).get('bp', {})

            if best_array_bp and roadwheel_diameter_m > 0 and belt_width_m > 0:
                roadwheel_array_bp = best_array_bp

                # Convert all to meters
                wheelDiameter = roadwheel_diameter_m
                wheelSpacing = roadwheel_array_bp.get('spacing', 0) / 1000.0

                # --- NEW: Use Explicit In-Game Count & Hard Limits ---
                unitCount = roadwheel_array_bp.get('count', 1)
                startingLength = roadwheel_array_bp.get('length', 0) / 1000.0
                xOffset = roadwheel_array_bp.get('xOffset', 0) / 1000.0
                usable_length = startingLength - xOffset

                # Extract Spacing Mode Variables
                spacingMode = roadwheel_array_bp.get('spacingMode', 0)
                interleaveFraction = roadwheel_array_bp.get('interleaveOverlapFraction', 0.5)
                groupSize = roadwheel_array_bp.get('perGroup', 1)
                groupOffset = roadwheel_array_bp.get('groupingOffset', 0)
                groupSpacing = roadwheel_array_bp.get('groupSpacing', 0) / 1000.0

                # 1. Determine Unit Footprint (W)
                bogie_internal_spacing = 0.0
                if suspension_type == 'HVSS':
                    bogie_internal_spacing = 1.325
                elif suspension_type == 'VVSS':
                    bogie_internal_spacing = 0.9
                elif suspension_type == 'leafSpring':
                    bogie_internal_spacing = 1.2

                unitWidth = wheelDiameter + (bogie_internal_spacing * suspension_scale)

                # 2. Determine Effective Spacing between units
                if spacingMode == 1:
                    overlap = wheelDiameter * interleaveFraction
                    effectiveSpacing = -overlap
                else:
                    effectiveSpacing = wheelSpacing

                # 3. Simulate Layout using Exact Count
                contact_length_m = 0.0
                if unitCount > 0:
                    currentPos = 0.0
                    wheelGroupPos = groupOffset

                    for i in range(unitCount):
                        # The physical footprint extends to the rear edge of this unit
                        contact_length_m = currentPos + unitWidth

                        # Add gaps for the NEXT unit (only if this isn't the last unit)
                        if i < unitCount - 1:
                            currentPos += unitWidth + effectiveSpacing
                            wheelGroupPos += 1

                            # Grouped Mode (2) adds an extra structural gap
                            if spacingMode == 2 and wheelGroupPos >= groupSize:
                                currentPos += groupSpacing
                                wheelGroupPos = 0

                # 4. Apply Absolute Game Limits
                # The contact length (flat track on the ground) cannot exceed the physical array bounds
                if contact_length_m > usable_length:
                    contact_length_m = usable_length

                # Failsafe: Contact length cannot be physically smaller than a single unit
                if contact_length_m < unitWidth:
                    contact_length_m = unitWidth

                if contact_length_m > 0:
                    contact_area_m2 = (contact_length_m - wheelDiameter) * belt_width_m * 2  # two tracks
                    contact_area_cm2 = contact_area_m2 * 10000.0
                    tank_weight_kg = stats["tank_weight"]

                    if contact_area_cm2 > 0:
                        ground_pressure = tank_weight_kg / contact_area_cm2

            stats["ground_pressure"] = ground_pressure
            stats["contact_length"] = contact_length_m - wheelDiameter
            stats["roadwheel_diam"] = wheelDiameter
            # 9. Fuel Tank Capacity
            total_fuel_liters = 0.0
            m_to_liters = 1000.0  # 1 m^3 = 1000 L

            for obj in blueprint_data.get('objects', []):
                # Check if this object is a fuel tank
                if "fuelTankBlueprintVuid" not in obj:
                    continue

                guid = obj.get('guid')
                if not guid:
                    continue

                try:
                    # 'scale' array directly represents dimensions in meters
                    scale = obj['transform']['scale']

                    if guid == "5e8ab5c7-e9f1-4c64-a04a-29efc78b1918":  # Square tank
                        # V = x * y * z
                        volume_m3 = scale[0] * scale[1] * scale[2]
                        total_fuel_liters += (volume_m3 * m_to_liters)

                    elif guid == "ecd3341c-f605-4816-946c-591eaa7e4f7d":  # Cylinder tank
                        # V = pi * r1 * r2 * h
                        # x/z are diameters, y is height
                        radius_m_x = scale[0] / 2.0
                        radius_m_z = scale[2] / 2.0
                        height_m = scale[1]

                        volume_m3 = math.pi * radius_m_x * radius_m_z * height_m
                        total_fuel_liters += (volume_m3 * m_to_liters)

                except Exception:
                    pass  # Ignore this fuel tank if something is wrong with its data

            stats["fuel_tank_capacity"] = total_fuel_liters

            # 10. Frontal Armor Angle
            upper_plate_angles = []
            lower_plate_angles = []
            z_tolerance = 0.05  # 5cm tolerance for what counts as "frontal"

            # Check all structure meshes (hull, turrets)
            for mesh_vuid, v_coords in all_vertices.items():
                mesh = meshes.get(mesh_vuid)
                if not mesh: continue

                faces = mesh.get("meshData", {}).get("mesh", {}).get("faces", [])
                for face in faces:
                    is_frontal = False
                    face_vertices_indices = face.get('v', [])
                    if len(face_vertices_indices) < 3:
                        continue

                    face_coords = []
                    for v_index in face_vertices_indices:
                        if v_index < len(v_coords):
                            coord = v_coords[v_index]
                            face_coords.append(coord)
                            # Use the globally found hull_max_z
                            if coord[2] >= (hull_max_z - z_tolerance):
                                is_frontal = True

                    if is_frontal:
                        # --- Size Filter ---
                        face_x_coords = [v[0] for v in face_coords]
                        face_y_coords = [v[1] for v in face_coords]
                        delta_x = max(face_x_coords) - min(face_x_coords)
                        delta_y = max(face_y_coords) - min(face_y_coords)

                        if delta_x < 0.1 or delta_y < 0.1:
                            continue  # Skip face, too small

                        # --- Angle Calculation ---
                        normal = self._get_face_normal(face_coords[0], face_coords[1], face_coords[2])
                        if normal is None or normal[2] < 0.1:  # Ignore internal or side-facing faces
                            continue

                        # ** FIX: Calculate angle from vertical (Y-axis) **
                        # Clamp normal[1] to avoid math domain errors from floating point inaccuracies
                        normal_y = np.clip(normal[1], -1.0, 1.0)
                        angle_from_y_axis = math.degrees(math.acos(normal_y))

                        # Convert to Sprocket's readout (0=vertical, 90=horizontal)
                        sprocket_angle = 90.0 - angle_from_y_axis

                        # --- Upper/Lower Split based on angle sign ---
                        if 0 <= sprocket_angle <= 90:
                            upper_plate_angles.append(sprocket_angle)
                        elif -90 <= sprocket_angle < 0:
                            lower_plate_angles.append(abs(sprocket_angle))

            # 9. D&D-Style RPG Stats Generation
            # Convert masses to tons to keep RPG numbers balanced (10-200 range instead of millions)
            weight_tons = stats.get("tank_weight", 0) / 1000.0
            armor_mass_tons = stats.get("armor_mass", 0) / 1000.0

            l = stats.get("tank_length", 0.5)
            w = stats.get("tank_width", 0.5)
            # Failsafe to grab highest available height metric
            h = stats.get("tank_total_height", stats.get("tank_height", 0.5))

            vol_factor = math.sqrt((h * w * l) + 1)
            print("vol", vol_factor)
            ke_mj = stats.get("ke_mj", 0)
            pen = stats.get("penetration", 0)
            mv = stats.get("muzzle_velocity", 0)
            top_speed = stats.get("top_speed", 0)
            gp = stats.get("ground_pressure", 0)

            # Hit Points & Damage
            stats["hit_points"] = int(weight_tons * vol_factor)
            stats["damage_rating"] = int(4 * (ke_mj + 3) - 11)

            # Penetration & Accuracy
            stats["penetration_rating"] = int((pen + (4 * ke_mj)) / 2)

            stats["accuracy_rating"] = int(10 / ((best_proj_mass ** 0.25) / (((math.pi * best_caliber/2 ** 2) * (ke_mj ** 2)) ** 0.1)) * (max_mv ** 0.5) if max_mv > 0 else 0)

            # Mobility
            mr = 0.0
            if vol_factor > 0:
                mr = (top_speed * 4) / (1 + gp) / (1 + (min(1.0, (w/l))))
            stats["mobility_rating"] = int(mr)

            # Armor Rating
            armor_div = min((4 * w) + l + h, 1)
            if armor_div > 0:
                # Using tons for armor mass so armor rating stays aligned with penetration scales
<<<<<<< Updated upstream
                #stats["armor_rating"] = int((80 * armor_mass_tons /(armor_mass_tons + weight_tons)) + (0.1 + weight_tons) + (0.2 * mr))
                stats["armor_rating"] = int((((weight_tons * (armor_mass_tons / weight_tons) + (0.1 * weight_tons))) * (mr)**(0.1)) / ((l * w + l * h + w * h) * 2)**(0.25)) * 10
            else:
                stats["armor_rating"] = int(0.1 * mr)

            return stats

        except Exception as e:
            print(f"Blueprint Analysis Error: {e}")
            return {'valid': False, 'error': str(e)}

    async def bakeGeometryV3(self, ctx: commands.Context, attachment):
        """
        Optimized version of bakeGeometry using NumPy vectorization and Matrix caching.
        """
        blueprintData = json.loads(await attachment.read())

        objects_by_vuid = {int(obj['vuid']): obj for obj in blueprintData['objects']}
        blueprints_by_id = {bp['id']: bp for bp in blueprintData['blueprints']}
        meshes_by_vuid = {mesh['vuid']: mesh for mesh in blueprintData['meshes']}

        transform_cache = {}

        final_vertices = []
        final_faces = []
        vertex_offset_counter = 0

        structures = [obj for obj in blueprintData['objects'] if "structureBlueprintVuid" in obj]

        for obj in structures:
            if "structureBlueprintVuid" not in obj:
                continue

            bp_id = obj['structureBlueprintVuid']
            bp = blueprints_by_id.get(bp_id)
            if not bp or bp['type'] != 'structure':
                continue

            mesh_vuid = bp['blueprint']['bodyMeshVuid']
            mesh_data_entry = meshes_by_vuid.get(mesh_vuid)

            if not mesh_data_entry:
                continue

            # Calculate Global Transform Matrix
            global_matrix = await self._get_world_transform(int(obj['vuid']), objects_by_vuid, transform_cache)

            # Process Mesh Vertices
            raw_verts = mesh_data_entry['meshData']['mesh']['vertices']
            raw_faces = mesh_data_entry['meshData']['mesh']['faces']

            if not raw_verts:
                continue

            vertices_np = numpy.array(raw_verts).reshape(-1, 3)

            # Homogeneous coords
            ones = numpy.ones((vertices_np.shape[0], 1))
            vertices_homogenous = numpy.hstack([vertices_np, ones])

            # Apply Transform: (N, 4) @ (4, 4).T -> (N, 4)
            transformed_verts = vertices_homogenous @ global_matrix.T

            xyz_verts = transformed_verts[:, :3]

            # Append Standard Vertices
            final_vertices.extend(xyz_verts.flatten().tolist())

            # Process Standard Faces
            for face in raw_faces:
                new_face = copy.copy(face)
                new_face['v'] = [idx + vertex_offset_counter for idx in face['v']]
                final_faces.append(new_face)

            vertex_offset_counter += len(vertices_np)

            # Handle Mirroring (Flag 6 or 7)
            # FIXED: Mirror logic now duplicates the WORLD SPACE vertices by flipping their X.
            # This ensures symmetry across the vehicle centerline (Hull X-axis).
            flags = int(obj.get("flags", 0))
            if flags in [6, 7]:
                xyz_mirror_verts = xyz_verts.copy()
                xyz_mirror_verts[:, 0] *= -1  # Flip World X

                final_vertices.extend(xyz_mirror_verts.flatten().tolist())

                # Handle Mirrored Faces (Flip Winding)
                for face in raw_faces:
                    new_face = copy.copy(face)
                    # Flip index order: [0, 1, 2] -> [0, 2, 1]
                    indices = [idx + vertex_offset_counter for idx in face['v']]
                    new_face['v'] = indices[::-1]
                    final_faces.append(new_face)

                vertex_offset_counter += len(xyz_mirror_verts)

        if len(blueprintData['meshes']) > 0:
            blueprintData['meshes'][0]['meshData']['mesh']['vertices'] = final_vertices
            blueprintData['meshes'][0]['meshData']['mesh']['faces'] = final_faces

        return blueprintData

    async def _get_world_transform(self, vuid: int, objects_by_vuid: dict, memo: dict) -> numpy.ndarray:
        """
        Recursively calculates the global transformation matrix for a specific object.
        Uses memoization to avoid re-calculating parents.
        """
        if vuid in memo:
            return memo[vuid]

        # Base case: Root of the tree (parent is -1)
        if vuid == -1:
            return numpy.identity(4)

        obj = objects_by_vuid[vuid]

        # 1. Local Translation
        pos = obj["transform"]["pos"]

        # 2. Local Rotation
        rot = obj["transform"]["rot"]

        rx, ry, rz = math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])

        # Manual matrix construction
        c, s = math.cos(rz), math.sin(rz)
        Mz = numpy.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

        c, s = math.cos(rx), math.sin(rx)
        Mx = numpy.array([[1, 0, 0], [0, c, -s], [0, s, c]])

        c, s = math.cos(ry), math.sin(ry)
        My = numpy.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

        # Order changed to My @ Mx @ Mz (matches V2 application order when Transposed)
        R_matrix = My @ Mx @ Mz

        # 3. Local Scale
        # FIX: Disabled scaling per user request.
        # This matches the behavior of V2 which ignored the "scale" parameter for structures.
        S_matrix = numpy.identity(3)

        # 4. Construct Local Transform Matrix (4x4)
        RS = R_matrix @ S_matrix

        local_matrix = numpy.identity(4)
        local_matrix[0:3, 0:3] = RS
        local_matrix[0:3, 3] = pos

        # 5. Get Parent Global Transform
        parent_vuid = int(obj["pvuid"])
        parent_matrix = await self._get_world_transform(parent_vuid, objects_by_vuid, memo)

        # 6. Global = Parent @ Local
        global_matrix = parent_matrix @ local_matrix

        memo[vuid] = global_matrix
        return global_matrix


async def runMeshTranslation(ctx: commands.Context, meshData, sourcePartInfo):
    sourcePartPosX = sourcePartInfo["pos"][0]
    sourcePartPosY = sourcePartInfo["pos"][1]
    sourcePartPosZ = sourcePartInfo["pos"][2]
    sourcePartRotX = math.radians(sourcePartInfo["rot"][0])
    sourcePartRotY = math.radians(sourcePartInfo["rot"][1])
    sourcePartRotZ = math.radians(sourcePartInfo["rot"][2])
    sourcePartPoints = meshData["meshData"]["mesh"]["vertices"]
    sourcePartPointsLength = len(sourcePartPoints)

    pos = 0
    # vector rotation
    while pos < sourcePartPointsLength:
        roundPoint = 6
        vector = [sourcePartPoints[pos], sourcePartPoints[pos + 1], sourcePartPoints[pos + 2]]
        angles = [-1 * sourcePartRotX, -1 * sourcePartRotY, -1 * sourcePartRotZ]

        newVector = braveRotateVector(vector, angles)

        sourcePartPoints[pos] = round(newVector[0] + sourcePartPosX, roundPoint)
        sourcePartPoints[pos + 1] = round(newVector[1] + sourcePartPosY, roundPoint)
        sourcePartPoints[pos + 2] = round(newVector[2] + sourcePartPosZ, roundPoint)
        pos += 3
    return sourcePartPoints


def braveRotateVector(vector, rot):
    import numpy as np
    rotX = rot[0]
    rotY = rot[1]
    rotZ = rot[2]
    # Define the rotation matrices for each plane
    matrixX = np.array([[1, 0, 0],
                        [0, np.cos(rotX), -np.sin(rotX)],
                        [0, np.sin(rotX), np.cos(rotX)]])

    matrixY = np.array([[np.cos(rotY), 0, np.sin(rotY)],
                        [0, 1, 0],
                        [-np.sin(rotY), 0, np.cos(rotY)]])

    matrixZ = np.array([[np.cos(rotZ), -np.sin(rotZ), 0],
                        [np.sin(rotZ), np.cos(rotZ), 0],
                        [0, 0, 1]])

    vector_xz = np.dot(vector, matrixZ)
    vector_xy = np.dot(vector_xz, matrixX)
    vector_yz = np.dot(vector_xy, matrixY)

    return vector_yz