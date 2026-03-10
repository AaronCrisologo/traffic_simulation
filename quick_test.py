"""Quick test of max-pressure algorithm"""
from simple_simulation import SimpleTrafficSimulator
from enhanced_config import EnhancedTrafficLightConfig

config = EnhancedTrafficLightConfig(
    min_green_time=12.0,
    max_green_time=30.0,
    arrival_rate=0.6,
    saturation_flow=2.8
)

sim = SimpleTrafficSimulator(config)

print("Testing max-pressure algorithm for 100 steps...")
for i in range(100):
    result = sim.update(delta_time=1.0)
    status = sim.controller.get_status()
    phase = status['current_phase']
    ns_green = status['phase_timings'].get('NS_GREEN', 0)
    ew_green = status['phase_timings'].get('EW_GREEN', 0)
    queues = result['queues']
    
    if i < 20 or (i + 1) % 10 == 0:
        print(f"Step {i+1:3d}: {phase:15s} NS_green={ns_green:5.1f}s EW_green={ew_green:5.1f}s | "
              f"N={queues['north']:3d} S={queues['south']:3d} E={queues['east']:3d} W={queues['west']:3d}")

print(f"\nTotal phases: {len(sim.controller.actual_phase_durations)}")
print("Test completed successfully!")
