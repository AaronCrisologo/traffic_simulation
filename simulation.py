"""
Traffic Intersection Simulation with Smart Light Control
Integrates CNN detection with adaptive traffic light timing
"""

import time
import random
from typing import Tuple
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from traffic_light_controller import TrafficLightController, TrafficLightConfig
from cnn_integration import CNNDetector


class TrafficIntersectionSimulation:
    """
    Main simulation class that coordinates:
    - CNN vehicle detection from 4 cameras
    - Adaptive traffic light control
    - Real-time visualization
    """
    
    def __init__(self, use_real_cnn: bool = False, simulation_speed: float = 1.0):
        self.controller = TrafficLightController()
        self.detector = CNNDetector()
        self.simulation_speed = simulation_speed
        self.running = False
        self.history = {
            'timestamps': [],
            'phases': [],
            'vehicle_counts': {'north': [], 'south': [], 'east': [], 'west': []},
            'green_times': {'ns': [], 'ew': []},
            'actual_phase_durations': []  # Track actual time spent in each phase
        }
        self.current_phase_start_time = None
        
    def run_step(self) -> dict:
        """Execute one simulation step"""
        current_time = time.time()

        # Get current phase before update
        old_phase = self.controller.current_phase

        # Determine which directions have green light
        green_directions = []
        if 'NS_GREEN' in old_phase.value or 'NS_YELLOW' in old_phase.value:
            green_directions.extend(['north', 'south'])
        if 'EW_GREEN' in old_phase.value or 'EW_YELLOW' in old_phase.value:
            green_directions.extend(['east', 'west'])

        # Update detector with current green phase
        if hasattr(self.detector, 'set_green_phase'):
            self.detector.set_green_phase(green_directions)

        # Get vehicle counts from CNN (simulated)
        north, south, east, west = self.detector.get_all_detections()

        # Update controller with new counts
        self.controller.update_vehicle_counts(north, south, east, west)

        # Update traffic light phase
        new_phase = self.controller.update()

        # Track phase duration if phase changed
        if self.current_phase_start_time is not None and old_phase != new_phase:
            phase_duration = current_time - self.current_phase_start_time
            self.history['actual_phase_durations'].append({
                'phase': old_phase.value,
                'duration': phase_duration
            })

        # Set start time for new phase
        if old_phase != new_phase:
            self.current_phase_start_time = current_time

        # Record data
        status = self.controller.get_status()
        self._record_step(status)

        return {
            'phase': new_phase,
        }
    
    def _record_step(self, status: dict):
        """Record simulation data for analysis"""
        self.history['timestamps'].append(time.time())
        self.history['phases'].append(status['current_phase'])
        
        counts = status['vehicle_counts']
        self.history['vehicle_counts']['north'].append(counts['north'])
        self.history['vehicle_counts']['south'].append(counts['south'])
        self.history['vehicle_counts']['east'].append(counts['east'])
        self.history['vehicle_counts']['west'].append(counts['west'])
        
        ns_green = status['phase_timings'].get('NS_GREEN', 0)
        ew_green = status['phase_timings'].get('EW_GREEN', 0)
        self.history['green_times']['ns'].append(ns_green)
        self.history['green_times']['ew'].append(ew_green)
    
    def _display_intersection(self, result: dict):
        """Display ASCII visualization of the intersection with enhanced stats"""
        phase = result['phase']
        vehicles = result['vehicles']
        remaining = result['status']['remaining_time']

        # Determine light colors based on phase (using ASCII for Windows compatibility)
        ns_color = "G" if "NS_GREEN" in phase.value else "Y" if "NS_YELLOW" in phase.value else "R"
        ew_color = "G" if "EW_GREEN" in phase.value else "Y" if "EW_YELLOW" in phase.value else "R"

        # Clear screen (cross-platform)
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        # North side
        print(f"        NORTH CAMERA")
        print(f"        Vehicles: {vehicles['north']:2d}")
        print(f"        Light: {ns_color} {phase.value}")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {ns_color}   |  <- NS")
        print("           |   v   |")
        print("           +-------+")
        print()

        # West-East row
        print(f"  WEST CAMERA: {vehicles['west']:2d}           EAST CAMERA: {vehicles['east']:2d}")
        print(f"  Light: {ew_color} {phase.value}           Light: {ew_color} {phase.value}")
        print()
        print("           +-------+")
        print("           |  <    |")
        print(f"           |   {ew_color}   |")
        print("           |   >   |")
        print("           +-------+")
        print()

        # South side
        print(f"        SOUTH CAMERA")
        print(f"        Vehicles: {vehicles['south']:2d}")
        print(f"        Light: {ns_color} {phase.value}")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {ns_color}   |  <- NS")
        print("           |   v   |")
        print("           +-------+")
        print(f"EW Green time: {result['status']['phase_timings'].get('EW_GREEN', 0):4.1f}s")
        print("=" * 60)
        
        # Enhanced performance display
        status = result['status']
        print(f"Efficiency: {status['performance']['efficiency']:5.1f}%")
        print(f"Throughput: {status['performance']['vehicle_throughput']:5.1f} vehicles/min")
        print(f"Avg Green Time: {status['performance']['average_green_time']:5.1f}s")
        print("=" * 60)

    def run_simulation(self, duration_seconds: float = 300):
        """Run simulation for specified duration"""
        print(f"Starting simulation for {duration_seconds} seconds...")
        print("Press Ctrl+C to stop early")
        time.sleep(2)

        self.running = True
        start_time = time.time()
        step_interval = 1.0 / self.simulation_speed

        try:
            while self.running and (time.time() - start_time) < duration_seconds:
                step_start = time.time()

                # Run simulation step
                result = self.run_step()

                # Display visual intersection
                self._display_intersection(result)

                # Wait for next step
                elapsed = time.time() - step_start
                sleep_time = max(0, step_interval - elapsed)
                time.sleep(sleep_time)

            print("\nSimulation complete!")
        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user.")
        finally:
            self.running = False

    def stop(self):
        """Stop the simulation"""
        self.running = False


def main():
    """Main entry point for the simulation"""
    print("=" * 60)
    print("SMART TRAFFIC LIGHT SIMULATION")
    print("Adaptive timing based on CNN vehicle detection")
    print("=" * 60)
    
    # Create simulation
    sim = TrafficIntersectionSimulation(simulation_speed=1.0)
    
    try:
        # Run for 5 minutes (300 seconds)
        sim.run_simulation(duration_seconds=300)
        
        # Generate plots
        print("\nGenerating analysis plots...")
        sim.plot_results()
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sim.stop()


if __name__ == "__main__":
    main()