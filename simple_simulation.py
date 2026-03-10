"""
Simple Traffic Light Simulation with Adaptive Timing
Terminal-based visualization of smart traffic light algorithm
"""

import time
import random
import os
from traffic_light_controller import TrafficLightController, TrafficLightConfig
from enhanced_config import EnhancedTrafficLightConfig


class SimpleTrafficSimulator:
    """
    Simplified traffic simulator that generates realistic traffic patterns
    and demonstrates the adaptive traffic light algorithm.
    """

    def __init__(self, controller_config: TrafficLightConfig = None):
        self.controller = TrafficLightController(controller_config)
        self.running = False

        # Simulated traffic state (queue lengths)
        self.queues = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }

        # Traffic generation parameters - use from config if available
        config = controller_config or TrafficLightConfig()
        self.arrival_rate = getattr(config, 'arrival_rate', 1.5)  # vehicles per second per direction
        self.saturation_flow = getattr(config, 'saturation_flow', 2.0)  # vehicles per second when green

        # History for analysis
        self.history = {
            'timestamps': [],
            'phases': [],
            'queues': {'north': [], 'south': [], 'east': [], 'west': []},
            'green_durations': {'ns': [], 'ew': []}
        }

    def _record_history(self):
        """Record current state for later analysis with enhanced metrics"""
        self.history['timestamps'].append(time.time())
        self.history['phases'].append(self.controller.current_phase.value)

        counts = self.get_vehicle_counts()
        self.history['queues']['north'].append(counts[0])
        self.history['queues']['south'].append(counts[1])
        self.history['queues']['east'].append(counts[2])
        self.history['queues']['west'].append(counts[3])

        # Record green times and performance metrics
        status = self.controller.get_status()
        ns_green = status['phase_timings'].get('NS_GREEN', 0)
        ew_green = status['phase_timings'].get('EW_GREEN', 0)
        self.history['green_durations']['ns'].append(ns_green)
        self.history['green_durations']['ew'].append(ew_green)

        # Record performance metrics
        self.history['performance'] = self.history.get('performance', {})
        self.history['performance']['timestamps'] = self.history['performance'].get('timestamps', [])
        self.history['performance']['efficiency'] = self.history['performance'].get('efficiency', [])
        self.history['performance']['throughput'] = self.history['performance'].get('throughput', [])
        self.history['performance']['timestamps'].append(time.time())
        self.history['performance']['efficiency'].append(status['performance']['efficiency'])
        self.history['performance']['throughput'].append(status['performance']['vehicle_throughput'])

    def generate_traffic(self, delta_time: float = 1.0):
        """Generate new vehicles arriving at each intersection with realistic patterns"""
        for direction in ['north', 'south', 'east', 'west']:
            # Use different arrival rates based on time of day simulation
            base_rate = self.arrival_rate
            if direction in ['north', 'south']:
                # Higher traffic on NS during peak hours
                peak_multiplier = 1.5 if (len(self.history['timestamps']) % 120) < 60 else 0.8
                arrivals = int(random.expovariate(1.0 / (base_rate * delta_time * peak_multiplier)))
            else:
                # Lower traffic on EW
                arrivals = int(random.expovariate(1.0 / (base_rate * delta_time * 0.7)))

            self.queues[direction] = int(self.queues[direction]) + arrivals

    def discharge_traffic(self, green_directions: list, delta_time: float = 1.0):
        """
        Remove vehicles from queues based on green light with discharge rate variation.
        Returns total vehicles discharged for tracking.
        """
        total_discharged = 0
        for direction in green_directions:
            # Vehicles leave at saturation flow rate with some variation
            base_discharge_rate = self.saturation_flow
            variation = random.uniform(0.8, 1.2)  # 20% variation in discharge rate
            discharge_rate = int(base_discharge_rate * delta_time * variation)
            discharged = min(int(self.queues[direction]), discharge_rate)
            self.queues[direction] -= discharged
            self.queues[direction] = max(0, int(self.queues[direction]))
            total_discharged += discharged
        return total_discharged

    def get_vehicle_counts(self) -> tuple:
        """Get current vehicle counts as integers"""
        return (
            int(self.queues['north']),
            int(self.queues['south']),
            int(self.queues['east']),
            int(self.queues['west'])
        )

    def update(self, delta_time: float = 1.0):
        """Execute one simulation step"""
        current_phase = self.controller.current_phase

        # Determine which directions have green (including yellow)
        green_directions = []
        if 'NS_GREEN' in current_phase.value or 'NS_YELLOW' in current_phase.value:
            green_directions.extend(['north', 'south'])
        if 'EW_GREEN' in current_phase.value or 'EW_YELLOW' in current_phase.value:
            green_directions.extend(['east', 'west'])

        # Generate new traffic (arrivals)
        self.generate_traffic(delta_time)

        # Discharge traffic from green directions and track count
        vehicles_discharged = self.discharge_traffic(green_directions, delta_time)

        # Get current counts and update controller
        north, south, east, west = self.get_vehicle_counts()
        self.controller.update_vehicle_counts(north, south, east, west)
        # Report vehicles processed to controller for throughput tracking
        self.controller.add_vehicles_processed(vehicles_discharged)

        # Update traffic light phase (pass delta_time for simulation time)
        new_phase = self.controller.update(delta_time)

        # Record history
        self._record_history()

        return {
            'phase': new_phase,
            'queues': self.queues.copy(),
            'counts': {'north': north, 'south': south, 'east': east, 'west': west}
        }

    def clear_screen(self):
        """Clear terminal screen (cross-platform)"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_intersection(self, result: dict):
        """Display ASCII visualization of the intersection with enhanced stats"""
        phase = result['phase']
        queues = result['queues']
        remaining = self.controller.get_remaining_time()

        # Determine light colors
        ns_color = "G" if "NS_GREEN" in phase.value else "Y" if "NS_YELLOW" in phase.value else "R"
        ew_color = "G" if "EW_GREEN" in phase.value else "Y" if "EW_YELLOW" in phase.value else "R"

        self.clear_screen()

        print("=" * 70)
        print(" " * 15 + "SMART TRAFFIC LIGHT SIMULATION")
        print("=" * 70)
        print()

        # North
        print(f"        NORTH: {queues['north']:3d} vehicles          Light: [{ns_color}] {phase.value}")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {ns_color}   |")
        print("           |   v   |")
        print("           +-------+")
        print()

        # West-East
        print(f"  WEST: {queues['west']:3d} vehicles                EAST: {queues['east']:3d} vehicles")
        print(f"  Light: [{ew_color}] {phase.value}            Light: [{ew_color}] {phase.value}")
        print()
        print("           +-------+")
        print("           |  <    |")
        print(f"           |   {ew_color}   |")
        print("           |   >   |")
        print("           +-------+")
        print()

        # South
        print(f"        SOUTH: {queues['south']:3d} vehicles          Light: [{ns_color}] {phase.value}")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {ns_color}   |")
        print("           |   v   |")
        print("           +-------+")
        print()

        # Performance metrics
        status = self.controller.get_status()
        print("=" * 70)
        print(f"Time remaining: {remaining:5.1f}s  |  Adaptive timing: ACTIVE")
        print(f"NS green time: {status['phase_timings'].get('NS_GREEN', 0):5.1f}s")
        print(f"EW green time: {status['phase_timings'].get('EW_GREEN', 0):5.1f}s")
        print(f"Efficiency: {status['performance']['efficiency']:5.1f}%")
        print(f"Throughput: {status['performance']['vehicle_throughput']:5.1f} vehicles/min")
        print("=" * 70)

    def print_statistics(self):
        """Print current statistics with enhanced metrics"""
        status = self.controller.get_status()
        print(f"\n[Stats] Phase: {status['current_phase']} | "
              f"NS: {self.queues['north'] + self.queues['south']:3d} | "
              f"EW: {self.queues['east'] + self.queues['west']:3d} | "
              f"NS Green: {status['phase_timings'].get('NS_GREEN', 0):4.1f}s | "
              f"EW Green: {status['phase_timings'].get('EW_GREEN', 0):4.1f}s | "
              f"Efficiency: {status['performance']['efficiency']:5.1f}% | "
              f"Throughput: {status['performance']['vehicle_throughput']:5.1f} vehicles/min")

    def print_summary(self):
        """Print simulation summary with comprehensive analysis"""
        print("\n" + "=" * 70)
        print("SIMULATION SUMMARY")
        print("=" * 70)

        total_steps = len(self.history['phases'])
        if total_steps == 0:
            print("No data collected.")
            return

        # Count phase durations
        ns_total = sum(d['duration'] for d in self.history['actual_phase_durations']
                      if 'NS_GREEN' in d['phase'])
        ew_total = sum(d['duration'] for d in self.history['actual_phase_durations']
                      if 'EW_GREEN' in d['phase'])

        print(f"Total simulation steps: {total_steps}")
        print(f"Total time: {sum(d['duration'] for d in self.history['actual_phase_durations']):.1f}s")
        print(f"North-South green time: {ns_total:.1f}s")
        print(f"East-West green time: {ew_total:.1f}s")
        print()
        print("Average queue lengths:")
        for direction in ['north', 'south', 'east', 'west']:
            avg_queue = sum(self.history['queues'][direction]) / total_steps
            print(f"  {direction.capitalize()}: {avg_queue:.1f} vehicles")
        print()
        print("Performance Metrics:")
        
        # Calculate average performance metrics
        if self.history['performance']['timestamps']:
            avg_efficiency = sum(self.history['performance']['efficiency']) / len(self.history['performance']['efficiency'])
            avg_throughput = sum(self.history['performance']['throughput']) / len(self.history['performance']['throughput'])
            print(f"  Average Efficiency: {avg_efficiency:.1f}%")
            print(f"  Average Throughput: {avg_throughput:.1f} vehicles/min")
        print("=" * 70)


def main():
    """Main entry point"""
    # Create configuration with enhanced parameters
    config = EnhancedTrafficLightConfig(
        min_green_time=12.0,
        max_green_time=45.0,
        yellow_time=3.5,
        all_red_time=2.0,
        vehicle_threshold=4,
        extension_per_vehicle=0.6,
        max_extension=18.0,
        gap_time=2.5,
        min_gap_time=1.0,
        arrival_rate=1.8,
        saturation_flow=2.2,
        max_queue_length=20,
        priority_boost=1.3,
        emergency_vehicle_detection=True,
        emergency_priority_time=30.0
    )

    # Create and run simulation
    sim = SimpleTrafficSimulator(config)

    try:
        sim.run(duration_seconds=120, step_interval=1.0)
    except KeyboardInterrupt:
        print("\nSimulation interrupted.")


if __name__ == "__main__":
    main()
