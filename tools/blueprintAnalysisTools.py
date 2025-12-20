import json
import math
import discord
import type_hintsfrom discord.ext import commands
import json
import random
import math
import io
from datetime import datetime
import numpy as np

class blueprintAnalysisTools:
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

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

    async def _parse_blueprint_stats(self, ctx: commands.Context, blueprint_data: dict) -> dict:
        """
        Parses the blueprint dictionary and extracts specified vehicle statistics.
        """
        try:
            stats = {}

            # --- Placeholders ---
            stats["vehicle_class"] = "Placeholder"
            # stats["vehicle_era"] = "Placeholder" # This will be calculated
            stats["host_id"] = 0
            stats["faction_id"] = 0
            stats["base_cost"] = 1000
            # stats["tank_height"] = 0.0 # This will be calculated
            # stats["tank_total_height"] = 0.0 # This will be calculated
            # stats["fuel_tank_capacity"] = 0.0 # This will be calculated
            stats["ground_pressure"] = 0.0  # This will be calculated
            # stats["horsepower"] = 0 # This will be calculated
            # stats["hpt"] = 0.0 # This will be calculated
            # stats["top_speed"] = 0 # This will be calculated
            stats["travel_range"] = 0
            stats["cannon_stats"] = "Placeholder"
            # stats["armor_mass"] = 0.0 # This will be calculated
            stats["upper_frontal_angle"] = 0.0  # This will be calculated
            stats["lower_frontal_angle"] = 0.0  # This will be calculated
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
            turret_ring_bp_vuids = {bp['id'] for bp in blueprint_data.get('blueprints', []) if bp['type'] == 'turretRing'}

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

            # --- 5. Powertrain, Era, and Chassis info ---
            cylinder_count = 2  # Default
            cylinder_displacement = 1.0  # Default
            total_armor_volume = 0.0

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

            best_array_bp = None
            roadwheel_diameter_m = -1.0

            # Find all wheel array *objects*
            for obj in blueprint_data.get('objects', []):
                # Find objects that are wheel arrays AND have a wheel attached
                if "wheelMountArrayBlueprintVuid" in obj and "sharedWheelBlueprintVuid" in obj:
                    array_bp_id = obj.get('wheelMountArrayBlueprintVuid')
                    wheel_bp_id = obj.get('sharedWheelBlueprintVuid')

                    # Check if this is a wheel we care about
                    if wheel_bp_id in wheel_diameters_m:
                        current_diameter_m = wheel_diameters_m[wheel_bp_id]

                        # We only want roadwheels, not return rollers (which are smaller)
                        if current_diameter_m > roadwheel_diameter_m:
                            roadwheel_diameter_m = current_diameter_m
                            # Now store the *blueprint* of the array
                            best_array_bp = blueprints.get(array_bp_id, {}).get('bp', {})

            if best_array_bp and roadwheel_diameter_m > 0 and belt_width_m > 0:
                # We found the correct roadwheel array, now use its stats
                roadwheel_array_bp = best_array_bp

                # Convert all to meters (diameters are already in m, others are mm)
                startingLength = roadwheel_array_bp.get('length', 0) / 1000.0  # e.g., 5949
                wheelDiameter = roadwheel_diameter_m  # e.g., 0.9
                wheelSpacing = roadwheel_array_bp.get('spacing', 0) / 1000.0  # e.g., 135
                groupSize = roadwheel_array_bp.get('perGroup', 1)  # e.g., 2
                groupOffset = roadwheel_array_bp.get('groupingOffset', 0)  # e.g., 0
                groupSpacing = roadwheel_array_bp.get('groupSpacing', 0) / 1000.0  # e.g., 250

                # Logic from contactlength command
                maxLength = startingLength + wheelSpacing + groupSpacing - wheelDiameter
                wheel = 1
                currentLength = -1 * wheelSpacing
                wheelGroupPos = groupOffset
                finalLength = 0

                while currentLength <= maxLength:
                    finalLength = currentLength
                    currentLength += wheelDiameter + wheelSpacing
                    wheel += 1
                    wheelGroupPos += 1
                    if wheelGroupPos == groupSize:
                        currentLength += groupSpacing
                        wheelGroupPos -= groupSize

                contact_length_m = finalLength + wheelSpacing

                if contact_length_m > 0:
                    contact_area_m2 = contact_length_m * belt_width_m * 2  # two tracks
                    contact_area_cm2 = contact_area_m2 * 10000.0
                    tank_weight_kg = stats["tank_weight"]

                    if contact_area_cm2 > 0:
                        ground_pressure = tank_weight_kg / contact_area_cm2

            stats["ground_pressure"] = ground_pressure

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

            stats["upper_frontal_angle"] = np.mean(upper_plate_angles) if upper_plate_angles else 0.0
            stats["lower_frontal_angle"] = np.mean(lower_plate_angles) if lower_plate_angles else 0.0

            return stats

        except Exception as e:
            print(f"Blueprint Analysis Error: {e}")
            return {'valid': False, 'error': str(e)}