import random
from aip_data import get_all_military_areas

def get_active_airspaces(flight_level_feet):
    areas = get_all_military_areas()
    sorted_names = sorted(areas.keys())
    num_areas = len(sorted_names)

    print(f"\n--- Airspace Activation Module ({flight_level_feet} feet) ---")

    # 1: Seed Selection 
    raw_seed = input("Enter a seed or press Enter for a random one: ").strip()
    
    if raw_seed:
        used_seed = raw_seed
        random.seed(used_seed)
        activation_states = [random.choice([True, False]) for _ in range(num_areas)]
        print(f"[INFO] Seed '{used_seed}' detected. Auto-generating scenario...")
    else:
        # NO SEED 
        used_seed = str(random.randint(1000, 9999))
        random.seed(used_seed) 
        
        while True:
            choice = input("Do you want to load a specific scenario? (y/n): ").strip().lower()
            if choice == 'y':
                print(f"Current areas: {sorted_names}")
                while True:
                    bitstring = input(f"Input {num_areas} bits (0/1): ").strip()
                    if len(bitstring) == num_areas and all(b in '01' for b in bitstring):
                        activation_states = [b == '1' for b in bitstring]
                        break
                    print(f"[ERROR] Please enter exactly {num_areas} bits.")
                break
            elif choice == 'n':
                activation_states = [random.choice([True, False]) for _ in range(num_areas)]
                break
            print("[ERROR] Please type 'y' or 'n'.")

    #2: Vertical Filtering 
    active_areas = []
    print("\n--- Final Activation Status ---")
    
    for i, name in enumerate(sorted_names):
        area = areas[name]
        is_requested = activation_states[i]
        is_in_altitude = area['lower_limit'] <= flight_level_feet <= area['upper_limit']
        
        if is_requested:
            if is_in_altitude:
                active_areas.append(area)
                print(f"[ACTIVE]   {name}")
            else:
                print(f"[REJECTED] {name}: Altitude {flight_level_feet} ft is outside bounds.")
        else:
            print(f"[OFF]      {name}")

    print(f"\nSummary: {len(active_areas)} active areas. Seed used: {used_seed}")
    return active_areas, used_seed

if __name__ == "__main__":
    get_active_airspaces(15000)