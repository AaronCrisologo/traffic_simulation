"""Test max-pressure algorithm with higher traffic load"""
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
    arrival_rate=1.2,      # Higher arrival rate
    saturation_flow=3.2,   # Higher discharge capacity
)

sim = SimpleTrafficSimulator(config)

print("=" * 100)
print("MAX-PRESSURE ALGORITHM TEST - Higher Traffic Load")
print("=" * 100)
print(f"{'Step':<6} {'Phase':<15} {'NS Green':<10} {'EW Green':<10} {'N':<4} {'S':<4} {'E':<4} {'W':<4} {'Throughput':<12}")
print("-" * 100)

for i in range(200):
    result = sim.update(delta_time=1.0)
    status = sim.controller.get_status()
    phase = status['current_phase']
    ns_green = status['phase_timings'].get('NS_GREEN', 0)
    ew_green = status['phase_timings'].get('EW_GREEN', 0)
    queues = result['queues']
    throughput = status['performance']['vehicle_throughput']
    
    # Show every 5 steps for readability
    if i < 20 or (i + 1) % 5 == 0:
        print(f"{i+1:<6} {phase:<15} {ns_green:<10.1f} {ew_green:<10.1f} "
              f"{queues['north']:<4} {queues['south']:<4} {queues['east']:<4} {queues['west']:<4} "
              f"{throughput:<12.1f}")

print("\n" + "=" * 100)
print("SUMMARY:")
print(f"Total phases completed: {len(sim.controller.actual_phase_durations)}")
print(f"Final queues: N={sim.queues['north']}, S={sim.queues['south']}, "
      f"E={sim.queues['east']}, W={sim.queues['west']}")
print(f"Total vehicles processed: {sim.controller.total_vehicles_processed}")
print(f"Average throughput: {status['performance']['vehicle_throughput']:.1f} vehicles/min")
print("=" * 100)
