"""
Simple test for advanced traffic controller
"""

from advanced_traffic_controller import AdvancedTrafficController, AdvancedTrafficConfig

def simple_test():
    print("Simple Advanced Controller Test")
    print("=" * 60)
    
    config = AdvancedTrafficConfig(
        min_green_time=10.0,
        max_green_time=30.0,
        yellow_time=3.0,
        all_red_time=2.0,
        vehicle_threshold=3,
        extension_per_vehicle=0.5,
        max_extension=10.0,
        gap_time=2.0
    )
    
    controller = AdvancedTrafficController(config)
    
    # Start with some vehicles
    controller.update_vehicle_counts(10, 5, 3, 8)
    
    print("Initial state:")
    status = controller.get_status()
    print(f"  Phase: {status['current_phase']}")
    print(f"  Queues: N={status['vehicle_counts']['north']}, S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, W={status['vehicle_counts']['west']}")
    print(f"  Pressures: N={status['pressures']['north']:.1f}, S={status['pressures']['south']:.1f}, "
          f"E={status['pressures']['east']:.1f}, W={status['pressures']['west']:.1f}")
    
    print("\nRunning simulation for 50 steps:")
    print("Step  Phase        Remaining  N   S   E   W")
    print("-" * 60)
    
    green_phases_seen = set()
    
    for step in range(50):
        phase = controller.update(1.0)
        status = controller.get_status()
        
        if phase.value.endswith('GREEN'):
            green_phases_seen.add(phase.value)
        
        # Print every 5 steps or when phase changes
        if step % 5 == 0 or step < 10:
            print(f"{step+1:4d}  {phase.value:10s} {status['remaining_time']:9.1f}s "
                  f"{status['vehicle_counts']['north']:3d} "
                  f"{status['vehicle_counts']['south']:3d} "
                  f"{status['vehicle_counts']['east']:3d} "
                  f"{status['vehicle_counts']['west']:3d}")
        
        # Simulate some traffic discharge when direction has green
        if phase.value == 'N_GREEN' and status['vehicle_counts']['north'] > 0:
            # Discharge 2 vehicles per second
            discharge = min(2, status['vehicle_counts']['north'])
            new_north = max(0, status['vehicle_counts']['north'] - discharge)
            controller.update_vehicle_counts(new_north, 
                                           status['vehicle_counts']['south'],
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['west'])
        elif phase.value == 'S_GREEN' and status['vehicle_counts']['south'] > 0:
            discharge = min(2, status['vehicle_counts']['south'])
            new_south = max(0, status['vehicle_counts']['south'] - discharge)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           new_south,
                                           status['vehicle_counts']['east'],
                                           status['vehicle_counts']['west'])
        elif phase.value == 'E_GREEN' and status['vehicle_counts']['east'] > 0:
            discharge = min(2, status['vehicle_counts']['east'])
            new_east = max(0, status['vehicle_counts']['east'] - discharge)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           status['vehicle_counts']['south'],
                                           new_east,
                                           status['vehicle_counts']['west'])
        elif phase.value == 'W_GREEN' and status['vehicle_counts']['west'] > 0:
            discharge = min(2, status['vehicle_counts']['west'])
            new_west = max(0, status['vehicle_counts']['west'] - discharge)
            controller.update_vehicle_counts(status['vehicle_counts']['north'],
                                           status['vehicle_counts']['south'],
                                           status['vehicle_counts']['east'],
                                           new_west)
    
    print(f"\nGreen phases seen: {sorted(green_phases_seen)}")
    
    # Final status
    status = controller.get_status()
    print(f"\nFinal queues: N={status['vehicle_counts']['north']}, S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, W={status['vehicle_counts']['west']}")
    print(f"Total processed: {status['performance']['vehicles_processed']} vehicles")
    print(f"By direction: {status['performance']['direction_processed']}")

if __name__ == "__main__":
    simple_test()