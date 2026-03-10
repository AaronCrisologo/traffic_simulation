"""
Comparison between old (NS/EW paired) and new (individual direction) systems
"""

import time
from traffic_light_controller import TrafficLightController, TrafficLightConfig
from advanced_traffic_controller import AdvancedTrafficController, AdvancedTrafficConfig


def run_old_system(scenario_name, north, south, east, west, steps=30):
    """Run the old NS/EW paired system"""
    print(f"\n{'='*60}")
    print(f"OLD SYSTEM: {scenario_name}")
    print(f"{'='*60}")
    
    config = TrafficLightConfig(
        min_green_time=12.0,
        max_green_time=45.0,
        yellow_time=3.5,
        all_red_time=2.0,
        vehicle_threshold=4,
        extension_per_vehicle=0.6,
        max_extension=15.0,
        gap_time=2.5
    )
    
    controller = TrafficLightController(config)
    controller.update_vehicle_counts(north, south, east, west)
    
    print(f"Initial: N={north}, S={south}, E={east}, W={west}")
    print(f"NS total: {north+south}, EW total: {east+west}")
    print("\nStep  Phase        NS Queue  EW Queue  NS Time  EW Time")
    print("-" * 60)
    
    for step in range(steps):
        phase = controller.update(1.0)
        status = controller.get_status()
        
        ns_queue = status['vehicle_counts']['north'] + status['vehicle_counts']['south']
        ew_queue = status['vehicle_counts']['east'] + status['vehicle_counts']['west']
        ns_time = status['phase_timings'].get('NS_GREEN', 0)
        ew_time = status['phase_timings'].get('EW_GREEN', 0)
        
        if step % 5 == 0 or 'GREEN' in phase.value:
            print(f"{step+1:4d}  {phase.value:12s} {ns_queue:9d} {ew_queue:9d} {ns_time:8.1f}s {ew_time:8.1f}s")
        
        # Simulate some traffic discharge
        if 'NS_GREEN' in phase.value:
            # Discharge from NS
            discharge_n = min(2, status['vehicle_counts']['north'])
            discharge_s = min(2, status['vehicle_counts']['south'])
            new_north = max(0, status['vehicle_counts']['north'] - discharge_n)
            new_south = max(0, status['vehicle_counts']['south'] - discharge_s)
            controller.update_vehicle_counts(new_north, new_south,
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['west'])
        elif 'EW_GREEN' in phase.value:
            # Discharge from EW
            discharge_e = min(2, status['vehicle_counts']['east'])
            discharge_w = min(2, status['vehicle_counts']['west'])
            new_east = max(0, status['vehicle_counts']['east'] - discharge_e)
            new_west = max(0, status['vehicle_counts']['west'] - discharge_w)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           status['vehicle_counts']['south'],
                                           new_east, new_west)
    
    status = controller.get_status()
    print(f"\nFinal: N={status['vehicle_counts']['north']}, S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, W={status['vehicle_counts']['west']}")
    print(f"Total processed: {status['performance']['vehicle_throughput']:.1f} veh/min")


def run_new_system(scenario_name, north, south, east, west, steps=30):
    """Run the new individual direction system"""
    print(f"\n{'='*60}")
    print(f"NEW SYSTEM: {scenario_name}")
    print(f"{'='*60}")
    
    config = AdvancedTrafficConfig(
        min_green_time=10.0,
        max_green_time=35.0,
        yellow_time=3.0,
        all_red_time=2.0,
        vehicle_threshold=3,
        extension_per_vehicle=0.7,
        max_extension=20.0,
        gap_time=2.0
    )
    
    controller = AdvancedTrafficController(config)
    controller.update_vehicle_counts(north, south, east, west)
    
    print(f"Initial: N={north}, S={south}, E={east}, W={west}")
    print("\nStep  Phase        N   S   E   W   Pressure  Green Time")
    print("-" * 60)
    
    for step in range(steps):
        phase = controller.update(1.0)
        status = controller.get_status()
        
        if step % 5 == 0 or 'GREEN' in phase.value:
            # Get pressure for current green direction (if any)
            current_dir = None
            if phase.value == 'N_GREEN':
                current_dir = 'north'
            elif phase.value == 'S_GREEN':
                current_dir = 'south'
            elif phase.value == 'E_GREEN':
                current_dir = 'east'
            elif phase.value == 'W_GREEN':
                current_dir = 'west'
            
            pressure = status['pressures'][current_dir] if current_dir else 0
            green_time = status['phase_timings'].get(f'{current_dir[0].upper()}_GREEN', 0) if current_dir else 0
            
            print(f"{step+1:4d}  {phase.value:10s} "
                  f"{status['vehicle_counts']['north']:3d} "
                  f"{status['vehicle_counts']['south']:3d} "
                  f"{status['vehicle_counts']['east']:3d} "
                  f"{status['vehicle_counts']['west']:3d} "
                  f"{pressure:9.1f} {green_time:10.1f}s")
        
        # Simulate traffic discharge
        if phase.value == 'N_GREEN' and status['vehicle_counts']['north'] > 0:
            discharge = min(2, status['vehicle_counts']['north'])
            new_north = max(0, status['vehicle_counts']['north'] - discharge)
            controller.update_vehicle_counts(new_north,
                                           status['vehicle_counts']['south'],
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['north'] - 2)
            controller.update_vehicle_counts(new_north,
                                           status['vehicle_counts']['south'],
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['west'])
        elif phase.value == 'S_GREEN' and status['vehicle_counts']['south'] > 0:
            new_south = max(0, status['vehicle_counts']['south'] - 2)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           new_south,
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['west'])
        elif phase.value == 'E_GREEN' and status['vehicle_counts']['east'] > 0:
            new_east = max(0, status['vehicle_counts']['east'] - 2)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           status['vehicle_counts']['south'],
                                           new_east,
                                           status['vehicle_counts']['west'])
        elif phase.value == 'W_GREEN' and status['vehicle_counts']['west'] > 0:
            new_west = max(0, status['vehicle_counts']['west'] - 2)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           status['vehicle_counts']['south'],
                                           status['vehicle_counts']['east'],
                                           new_west)
    
    status = controller.get_status()
    print(f"\nFinal: N={status['vehicle_counts']['north']}, S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, W={status['vehicle_counts']['west']}")
    print(f"Total processed: {status['performance']['throughput']:.1f} veh/min")


def compare_scenarios():
    """Compare both systems on different scenarios"""
    scenarios = [
        ("Heavy North, Light Others", 20, 5, 3, 2),
        ("Balanced Traffic", 10, 8, 9, 7),
        ("East-West Dominant", 3, 4, 15, 12),
        ("Single Direction Heavy", 25, 2, 1, 1),
    ]
    
    print("SYSTEM COMPARISON: Old (NS/EW pairs) vs New (Individual directions)")
    print("=" * 80)
    
    for scenario_name, n, s, e, w in scenarios:
        print(f"\n\n{'#'*80}")
        print(f"SCENARIO: {scenario_name}")
        print(f"Initial queues: N={n}, S={s}, E={e}, W={w}")
        print(f"{'#'*80}")
        
        run_old_system(scenario_name, n, s, e, w, steps=25)
        run_new_system(scenario_name, n, s, e, w, steps=25)
        
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print("\nKey Differences:")
    print("1. OLD SYSTEM: Treats N+S and E+W as pairs")
    print("   - Pros: Simpler, fewer phase transitions")
    print("   - Cons: Wastes time when one direction in pair is empty")
    print("   - Best for: Symmetric traffic patterns")
    
    print("\n2. NEW SYSTEM: Treats each direction separately")
    print("   - Pros: More precise, adapts to asymmetric traffic")
    print("   - Cons: More phase transitions, slightly more complex")
    print("   - Best for: Asymmetric traffic, rush hour patterns")
    
    print("\n3. When to use which:")
    print("   - Use OLD system for: Standard intersections, balanced traffic")
    print("   - Use NEW system for: Problem intersections, heavy directional flows")
    print("   - Use NEW system when: One direction consistently has more traffic")


if __name__ == "__main__":
    compare_scenarios()