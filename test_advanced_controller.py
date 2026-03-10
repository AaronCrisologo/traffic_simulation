"""
Test script for Advanced Traffic Controller
Verifies that individual direction control works correctly
"""

import time
from advanced_traffic_controller import AdvancedTrafficController, AdvancedTrafficConfig


def test_basic_functionality():
    """Test basic controller functionality"""
    print("=" * 60)
    print("Testing Advanced Traffic Controller")
    print("=" * 60)
    
    # Create configuration
    config = AdvancedTrafficConfig(
        min_green_time=10.0,
        max_green_time=30.0,
        yellow_time=3.0,
        all_red_time=2.0,
        vehicle_threshold=3,
        extension_per_vehicle=0.5,
        max_extension=15.0
    )
    
    # Create controller
    controller = AdvancedTrafficController(config)
    
    print("\n1. Initial State:")
    status = controller.get_status()
    print(f"   Current phase: {status['current_phase']}")
    print(f"   Vehicle counts: {status['vehicle_counts']}")
    print(f"   Phase timings: {status['phase_timings']}")
    
    # Test 1: Update with no vehicles
    print("\n2. Testing with no vehicles:")
    controller.update_vehicle_counts(0, 0, 0, 0)
    for i in range(5):
        phase = controller.update(1.0)
        status = controller.get_status()
        print(f"   Step {i+1}: Phase={phase.value}, Remaining={status['remaining_time']:.1f}s")
    
    # Test 2: Add vehicles to North direction
    print("\n3. Testing with vehicles in North direction:")
    controller.update_vehicle_counts(10, 0, 0, 0)
    status = controller.get_status()
    print(f"   North queue: {status['vehicle_counts']['north']}")
    print(f"   North green time: {status['phase_timings'].get('N_GREEN', 0):.1f}s")
    print(f"   North pressure: {status['pressures']['north']:.1f}")
    
    # Run a few steps
    for i in range(8):
        phase = controller.update(1.0)
        if phase.value == 'N_GREEN':
            print(f"   Step {i+1}: North got GREEN!")
            break
    
    # Test 3: Test pressure calculation with different queues
    print("\n4. Testing pressure calculation:")
    controller.update_vehicle_counts(15, 5, 3, 8)
    status = controller.get_status()
    print(f"   Queues: N={status['vehicle_counts']['north']}, S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, W={status['vehicle_counts']['west']}")
    print(f"   Pressures: N={status['pressures']['north']:.1f}, S={status['pressures']['south']:.1f}, "
          f"E={status['pressures']['east']:.1f}, W={status['pressures']['west']:.1f}")
    
    # Test 4: Test phase selection
    print("\n5. Testing phase selection algorithm:")
    print("   Running 20 steps to see phase transitions...")
    
    phases_seen = set()
    for i in range(20):
        phase = controller.update(1.0)
        phases_seen.add(phase.value)
        if i % 5 == 0:
            status = controller.get_status()
            print(f"   Step {i+1}: {phase.value:10s} | "
                  f"N:{status['vehicle_counts']['north']:2d}({status['pressures']['north']:4.1f}) "
                  f"S:{status['vehicle_counts']['south']:2d}({status['pressures']['south']:4.1f}) "
                  f"E:{status['vehicle_counts']['east']:2d}({status['pressures']['east']:4.1f}) "
                  f"W:{status['vehicle_counts']['west']:2d}({status['pressures']['west']:4.1f})")
    
    print(f"\n   Unique phases seen: {sorted(phases_seen)}")
    
    # Test 5: Performance metrics
    print("\n6. Performance metrics:")
    status = controller.get_status()
    perf = status['performance']
    print(f"   Efficiency: {perf['efficiency']:.1f}%")
    print(f"   Throughput: {perf['throughput']:.1f} veh/min")
    print(f"   Total processed: {perf['vehicles_processed']} vehicles")
    print(f"   By direction: {perf['direction_processed']}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


def test_scenario(scenario_name, north, south, east, west, steps=30):
    """Test a specific traffic scenario"""
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario_name}")
    print(f"{'='*60}")
    
    config = AdvancedTrafficConfig()
    controller = AdvancedTrafficController(config)
    
    # Set initial vehicle counts
    controller.update_vehicle_counts(north, south, east, west)
    
    print(f"Initial queues: N={north}, S={south}, E={east}, W={west}")
    print("\nStep  Phase        N   S   E   W   Pressure(N) Next Green")
    print("-" * 60)
    
    last_green = None
    for step in range(steps):
        # Update controller
        phase = controller.update(1.0)
        status = controller.get_status()
        
        # Determine which direction will likely get green next
        next_green = "?"
        if phase.value == 'ALL_RED':
            # Check pressures to predict next green
            pressures = status['pressures']
            max_dir = max(pressures.keys(), key=lambda d: pressures[d])
            next_green = max_dir[0].upper()  # First letter
        
        # Print step info
        if step % 3 == 0 or phase.value.endswith('GREEN'):
            print(f"{step+1:4d}  {phase.value:10s} "
                  f"{status['vehicle_counts']['north']:3d} "
                  f"{status['vehicle_counts']['south']:3d} "
                  f"{status['vehicle_counts']['east']:3d} "
                  f"{status['vehicle_counts']['west']:3d} "
                  f"{status['pressures']['north']:10.1f}  {next_green}")
        
        # Track green phases
        if phase.value.endswith('GREEN'):
            last_green = phase.value
    
    # Final summary
    status = controller.get_status()
    print(f"\nFinal queues: N={status['vehicle_counts']['north']}, "
          f"S={status['vehicle_counts']['south']}, "
          f"E={status['vehicle_counts']['east']}, "
          f"W={status['vehicle_counts']['west']}")
    print(f"Total processed: {status['performance']['vehicles_processed']} vehicles")


def run_scenarios():
    """Run multiple test scenarios"""
    scenarios = [
        ("Heavy North Traffic", 20, 5, 3, 2),
        ("Balanced Traffic", 8, 7, 9, 6),
        ("East-West Dominant", 2, 3, 15, 12),
        ("Single Direction Heavy", 25, 1, 1, 1),
        ("All Directions Equal", 10, 10, 10, 10),
    ]
    
    for scenario in scenarios:
        test_scenario(scenario[0], scenario[1], scenario[2], scenario[3], scenario[4])
        time.sleep(1)


if __name__ == "__main__":
    print("Advanced Traffic Controller Test Suite")
    print("Testing individual direction control algorithm")
    print()
    
    # Run basic functionality test
    test_basic_functionality()
    
    print("\n\n" + "="*60)
    print("Running Scenario Tests")
    print("="*60)
    
    # Run scenario tests
    run_scenarios()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)