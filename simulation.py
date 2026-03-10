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
            'green_times': {'ns': [], 'ew': []}
        }
        
    def run_step(self) -> dict:
        """Execute one simulation step"""
        # Get current phase before update
        current_phase = self.controller.current_phase
        
        # Determine which directions have green light
        green_directions = []
        if 'NS_GREEN' in current_phase.value or 'NS_YELLOW' in current_phase.value:
            green_directions.extend(['north', 'south'])
        if 'EW_GREEN' in current_phase.value or 'EW_YELLOW' in current_phase.value:
            green_directions.extend(['east', 'west'])
        
        # Update detector with current green phase
        if hasattr(self.detector, 'set_green_phase'):
            self.detector.set_green_phase(green_directions)
        
        # Get vehicle counts from CNN (simulated)
        north, south, east, west = self.detector.get_all_detections()
        
        # Update controller with new counts
        self.controller.update_vehicle_counts(north, south, east, west)
        
        # Update traffic light phase
        current_phase = self.controller.update()
        
        # Record data
        status = self.controller.get_status()
        self._record_step(status)
        
        return {
            'phase': current_phase,
            'vehicles': {'north': north, 'south': south, 'east': east, 'west': west},
            'status': status
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
        
    def _print_status(self, result: dict):
        """Print current simulation status"""
        phase = result['phase'].value
        vehicles = result['vehicles']
        remaining = result['status']['remaining_time']
        
        print(f"\rPhase: {phase:20} | "
              f"N:{vehicles['north']:2d} S:{vehicles['south']:2d} "
              f"E:{vehicles['east']:2d} W:{vehicles['west']:2d} | "
              f"Remaining: {remaining:4.1f}s", end="", flush=True)
    
    def _display_intersection(self, result: dict):
        """Display ASCII visualization of the intersection"""
        phase = result['phase']
        vehicles = result['vehicles']
        remaining = result['status']['remaining_time']
        
        # Determine light colors based on phase
        ns_color = "🟢" if "NS_GREEN" in phase.value else "🟡" if "NS_YELLOW" in phase.value else "🔴"
        ew_color = "🟢" if "EW_GREEN" in phase.value else "🟡" if "EW_YELLOW" in phase.value else "🔴"
        
        # Clear screen and display
        print("\033c", end="")  # Clear terminal
        
        print("=" * 60)
        print("      SMART TRAFFIC LIGHT SIMULATION")
        print("=" * 60)
        print()
        
        # North side
        print(f"        NORTH CAMERA")
        print(f"        Vehicles: {vehicles['north']:2d}")
        print(f"        Light: {ns_color} {phase.value}")
        print()
        print("           ┌─────────┐")
        print("           │    ↑    │")
        print(f"           │   {ns_color}   │  ← NS")
        print("           │    ↓    │")
        print("           └─────────┘")
        print()
        
        # West-East row
        print(f"  WEST CAMERA: {vehicles['west']:2d}           EAST CAMERA: {vehicles['east']:2d}")
        print(f"  Light: {ew_color} {phase.value}           Light: {ew_color} {phase.value}")
        print()
        print("           ┌─────────┐           ┌─────────┐")
        print("           │    ←    │           │    →    │")
        print(f"           │   {ew_color}   │           │   {ew_color}   │")
        print("           │    →    │           │    ←    │")
        print("           └─────────┘           └─────────┘")
        print()
        
        # South side
        print(f"        SOUTH CAMERA")
        print(f"        Vehicles: {vehicles['south']:2d}")
        print(f"        Light: {ns_color} {phase.value}")
        print()
        print("           ┌─────────┐")
        print("           │    ↑    │")
        print(f"           │   {ns_color}   │  ← NS")
        print("           │    ↓    │")
        print("           └─────────┘")
        print()
        
        print("=" * 60)
        print(f"Time in phase: {remaining:4.1f}s | Adaptive timing active")
        print(f"NS Green time: {result['status']['phase_timings'].get('NS_GREEN', 0):4.1f}s")
        print(f"EW Green time: {result['status']['phase_timings'].get('EW_GREEN', 0):4.1f}s")
        print("=" * 60)
        
    def plot_results(self):
        """Generate plots of simulation results"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Plot 1: Vehicle counts over time
        ax1 = axes[0]
        for direction in ['north', 'south', 'east', 'west']:
            ax1.plot(self.history['vehicle_counts'][direction], label=direction.capitalize())
        ax1.set_ylabel('Vehicle Count')
        ax1.set_title('Vehicle Detection from 4 Cameras')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Traffic light phases
        ax2 = axes[1]
        phases_numeric = [0 if 'NS' in p else 1 for p in self.history['phases']]
        ax2.plot(phases_numeric, drawstyle='steps-post', linewidth=2)
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['NS Green', 'EW Green'])
        ax2.set_ylabel('Phase')
        ax2.set_title('Traffic Light Phase Changes')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Adaptive green times
        ax3 = axes[2]
        ax3.plot(self.history['green_times']['ns'], label='NS Green', linewidth=2)
        ax3.plot(self.history['green_times']['ew'], label='EW Green', linewidth=2)
        ax3.set_ylabel('Duration (seconds)')
        ax3.set_xlabel('Time Step')
        ax3.set_title('Adaptive Green Time Adjustments')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
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