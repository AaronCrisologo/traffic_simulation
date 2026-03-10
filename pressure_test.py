"""Test max-pressure algorithm with higher traffic load"""
import time
import random
from simple_simulation import SimpleTrafficSimulator
from enhanced_config import EnhancedTrafficLightConfig

config = EnhancedTrafficLightConfig(
    min_green_time=12.0,
    max_green_time=60.0,
    yellow_time=3.5,
    all_red_time=2.0,
    vehicle_threshold=4,
    extension_per_vehicle=0.6,
    max_extension=15.0,
    gap_time=2.5,
    arrival_rate=2.5,      # Very high arrival rate - intensive traffic
    saturation_flow=2.5,   # Lower discharge capacity - creates congestion
)

sim = SimpleTrafficSimulator(config)

print("=" * 100)
print("MAX-PRESSURE ALGORITHM TEST - Higher Traffic Load")
print("=" * 100)
print(f"{'Step':<6} {'Phase':<15} {'NS Green':<10} {'EW Green':<10} {'N':<4} {'S':<4} {'E':<4} {'W':<4} {'Throughput':<12}")
print("-" * 100)

for i in range(200):
    # Dynamic arrival rate: mostly below discharge (2.5), occasional brief spikes
    base_rate = 1.0  # average arrival rate - comfortably below saturation flow
    
    # Add random daily cycle (simulating rush hours)
    cycle_position = i % 120  # 2-hour cycle in simulation time
    if cycle_position < 30:  # Morning rush
        cycle_multiplier = 1.3
    elif cycle_position < 90:  # Normal daytime
        cycle_multiplier = 1.0
    else:  # Evening rush
        cycle_multiplier = 1.2
    
    # Random fluctuation (±15%)
    random_factor = random.uniform(0.85, 1.15)
    
    # Rare congestion spike (5% chance, smaller magnitude)
    spike = 1.4 if random.random() < 0.05 else 1.0
    
    # Calculate dynamic arrival rate
    dynamic_rate = base_rate * cycle_multiplier * random_factor * spike
    
    # Apply to simulator
    sim.arrival_rate = dynamic_rate
    
    result = sim.update(delta_time=1.0)
    status = sim.controller.get_status()
    phase = status['current_phase']
    ns_green = status['phase_timings'].get('NS_GREEN', 0)
    ew_green = status['phase_timings'].get('EW_GREEN', 0)
    queues = result['queues']
    throughput = status['performance']['vehicle_throughput']
    
    # Show every step
    print(f"{i+1:<6} {phase:<15} {ns_green:<10.1f} {ew_green:<10.1f} "
          f"{queues['north']:<4} {queues['south']:<4} {queues['east']:<4} {queues['west']:<4} "
          f"{throughput:<12.1f}")
    time.sleep(0.2)  # 200ms delay between prints

print("\n" + "=" * 100)
print("SUMMARY:")
print(f"Total phases completed: {len(sim.controller.actual_phase_durations)}")
print(f"Final queues: N={sim.queues['north']}, S={sim.queues['south']}, "
      f"E={sim.queues['east']}, W={sim.queues['west']}")
print(f"Total vehicles processed: {sim.controller.total_vehicles_processed}")
print(f"Average throughput: {status['performance']['vehicle_throughput']:.1f} vehicles/min")
print("=" * 100)
