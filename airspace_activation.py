import random
from aip_data import get_all_military_areas

def get_seed_from_user():
    raw_seed = input("Enter a seed or press Enter for a random one: ").strip()
    return raw_seed if raw_seed else None

def get_activation_config(num_areas, sorted_names, seed=None):

    if seed:
        used_seed = seed
        random.seed(used_seed)
        activation_states = [random.choice([True, False]) for _ in range(num_areas)]
        print(f"[INFO] Auto-generating from seed: {used_seed}")
    else:
        # No seed provided then ask for specific scenario
        used_seed = str(random.randint(1000, 9999))
        random.seed(used_seed)
        
        while True:
            choice = input("Do you want to load a specific scenario? (y/n): ").strip().lower()
            if choice == 'y':
                print(f"Current areas: {sorted_names}")
                while True:
                    bits = input(f"Input {num_areas} bits: ").strip()
                    if len(bits) == num_areas and all(b in '01' for b in bits):
                        activation_states = [b == '1' for b in bits]
                        break
                    print(f"[ERROR] Enter {num_areas} bits.")
                break
            elif choice == 'n':
                activation_states = [random.choice([True, False]) for _ in range(num_areas)]
                break
            print("[ERROR] Please type 'y' or 'n'.")
            
    return activation_states, used_seed

def get_active_airspaces(flight_level_feet, activation_states):
    areas = get_all_military_areas()
    sorted_names = sorted(areas.keys())
    active_areas = []

    print(f"\n--- Processing Airspaces for {flight_level_feet} ft ---")
    for i, name in enumerate(sorted_names):
        area = areas[name]
        if activation_states[i]:
            if area['lower_limit'] <= flight_level_feet <= area['upper_limit']:
                active_areas.append(area)
                print(f"[ACTIVE]   {name}")
            else:
                print(f"[REJECTED] {name}: Outside altitude bounds.")
        else:
            print(f"[OFF]      {name}")
            
    return active_areas

if __name__ == "__main__":
    alt = 27000
    all_areas = get_all_military_areas()
    names = sorted(all_areas.keys())
    user_seed = get_seed_from_user()
    states, final_seed = get_activation_config(len(names), names, seed=user_seed)
    final_zones = get_active_airspaces(alt, states)
    
    print(f"\nFinal Result: {len(final_zones)} zones | Seed: {final_seed}")