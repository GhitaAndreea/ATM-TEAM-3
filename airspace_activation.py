import random
from aip_data import get_all_military_areas

def get_active_airspaces(flight_level, seed=None):
    if seed is not None: random.seed(seed)
    
    areas = get_all_military_areas()
    sorted_names = sorted(areas.keys())
    num_areas = len(sorted_names)
    
    print(f"\n--- Airspace Activation Module (FL{flight_level}) ---")

    # 1: Scenario Selection 
    while True:
        choice = input("Do you want to load a specific scenario? (y/n): ").strip().lower()
        
        if choice == 'n':
            activation_states = [random.choice([True, False]) for _ in range(num_areas)]
            break 
            
        elif choice == 'y':
            print(f"Current areas: {sorted_names}")
            bitstring = input(f"Input {num_areas} bits (e.g., {'0'*num_areas}): ").strip()
            
            # Validation: bits only (0 or 1) and correct length
            if len(bitstring) == num_areas and all(bit in '01' for bit in bitstring):
                activation_states = [bit == '1' for bit in bitstring]
                break 
            else:
                print(f"[ERROR] Invalid input. Please enter exactly {num_areas} bits (0 or 1).")
        else:
            print("[ERROR] Invalid command. Please type 'y' for Yes or 'n' for No.")

    #2: Processing & Vertical Filtering 
    active_areas = []
    print("\n--- Activation Status ---")
    for i, name in enumerate(sorted_names):
        area = areas[name]
        is_requested = activation_states[i]
        is_in_altitude = area['lower_limit'] <= flight_level <= area['upper_limit']
        
        if is_requested:
            if is_in_altitude:
                active_areas.append(area)
                print(f"[ACTIVE]  {name}")
            else:
                print(f"[REJECTED] {name}: Plane at {flight_level}ft is outside limits ({area['lower_limit']}-{area['upper_limit']}ft)")
        else:
            print(f"[OFF]     {name}")

    print(f"\nTotal active areas: {len(active_areas)}")
    return active_areas

if __name__ == "__main__":
    # Test with FL 15000
    get_active_airspaces(15000)