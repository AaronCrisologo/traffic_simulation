"""
Advanced Traffic Simulation with Individual Direction Control
Simulates a 4-way intersection where each direction (N, S, E, W) has separate timing
"""

import time
import random
import os
from advanced_traffic_controller import AdvancedTrafficController, AdvancedTrafficConfig


class AdvancedTrafficSimulator:
    """
    Advanced traffic simulator with individual direction control.
    Each direction (N, S, E, W) has separate green light timing.
    """
    
    def __init__(self, controller_config: AdvancedTrafficConfig = None):
        self.controller = AdvancedTrafficController(controller_config)
        
        # Simulated traffic queues for each direction
        self.queues = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Traffic generation parameters
        config = controller_config or AdvancedTrafficConfig()
        self.arrival_rate = 0.3  # vehicles per second per direction (base) - sustainable rate
        self.saturation_flow = 2.0  # vehicles per second when green
        
        # History for analysis
        self.history = {
            'timestamps': [],
            'phases': [],
            'queues': {'north': [], 'south': [], 'east': [], 'west': []},
            'green_times': {'north': [], 'south': [], 'east': [], 'west': []},
            'pressures': {'north': [], 'south': [], 'east': [], 'west': []}
        }
        
        # Performance metrics
        self.step_count = 0
    
    def generate_traffic(self, delta_time: float = 1.0):
        """Generate new vehicles arriving at each intersection"""
        # Time-of-day pattern simulation
        cycle_position = self.step_count % 120  # 2-minute cycle
        
        if cycle_position < 30:  # Morning rush (steps 0-29)
            time_multiplier = 1.4
        elif cycle_position < 90:  # Normal daytime (steps 30-89)
            time_multiplier = 1.0
        else:  # Evening rush (steps 90-119)
            time_multiplier = 1.3
        
        # Generate traffic for each direction with some variation
        for direction in ['north', 'south', 'east', 'west']:
            # Base arrival rate with time-of-day adjustment
            base_rate = self.arrival_rate * time_multiplier
            
            # Direction-specific variation (±20%)
            direction_factor = random.uniform(0.8, 1.2)
            
            # Random fluctuation
            random_factor = random.uniform(0.9, 1.1)
            
            # Calculate effective arrival rate
            effective_rate = base_rate * direction_factor * random_factor
            
            # Generate arrivals using Poisson process approximation
            # Expected arrivals = rate * time
            expected_arrivals = effective_rate * delta_time
            # Use Poisson distribution approximation (numpy would be better, but using simple approximation)
            # For small expected_arrivals, use binomial approximation
            if expected_arrivals < 10:
                # Simple approximation for Poisson
                arrivals = 0
                for _ in range(100):
                    if random.random() < expected_arrivals / 100:
                        arrivals += 1
            else:
                # For larger values, use normal approximation
                arrivals = int(max(0, random.normalvariate(expected_arrivals, expected_arrivals**0.5)))
            
            self.queues[direction] += arrivals
    
    def discharge_traffic(self, green_direction: str, delta_time: float = 1.0) -> int:
        """
        Remove vehicles from queue for the green direction.
        Returns number of vehicles discharged.
        """
        if green_direction not in self.queues:
            return 0
        
        # Calculate discharge based on saturation flow with some variation
        base_discharge = self.saturation_flow * delta_time
        variation = random.uniform(0.85, 1.15)  # 15% variation
        discharge_capacity = int(base_discharge * variation)
        
        # Discharge vehicles
        discharged = min(self.queues[green_direction], discharge_capacity)
        self.queues[green_direction] -= discharged
        
        # Ensure non-negative
        self.queues[green_direction] = max(0, self.queues[green_direction])
        
        return discharged
    
    def update(self, delta_time: float = 1.0) -> dict:
        """Execute one simulation step"""
        self.step_count += 1
        
        # Generate new traffic
        self.generate_traffic(delta_time)
        
        # Get current phase
        current_phase = self.controller.current_phase
        phase_str = current_phase.value
        
        # Determine which direction has green (if any)
        green_direction = None
        if phase_str == 'N_GREEN':
            green_direction = 'north'
        elif phase_str == 'S_GREEN':
            green_direction = 'south'
        elif phase_str == 'E_GREEN':
            green_direction = 'east'
        elif phase_str == 'W_GREEN':
            green_direction = 'west'
        
        # Discharge traffic from green direction
        vehicles_discharged = 0
        if green_direction:
            vehicles_discharged = self.discharge_traffic(green_direction, delta_time)
            # Report actual discharged vehicles to controller for accurate metrics
            if vehicles_discharged > 0:
                self.controller.add_vehicles_processed(green_direction, vehicles_discharged)
        
        # Update controller with current vehicle counts
        self.controller.update_vehicle_counts(
            self.queues['north'],
            self.queues['south'],
            self.queues['east'],
            self.queues['west']
        )
        
        # Advance traffic light controller
        new_phase = self.controller.update(delta_time)
        
        # Record history
        self._record_history(vehicles_discharged)
        
        return {
            'phase': new_phase,
            'green_direction': green_direction,
            'vehicles_discharged': vehicles_discharged,
            'queues': self.queues.copy(),
            'pressures': self.controller.get_status()['pressures']
        }
    
    def _record_history(self, vehicles_discharged: int):
        """Record current state for analysis"""
        self.history['timestamps'].append(time.time())
        
        # Record phase
        self.history['phases'].append(self.controller.current_phase.value)
        
        # Record queues
        for direction in ['north', 'south', 'east', 'west']:
            self.history['queues'][direction].append(self.queues[direction])
        
        # Record green times for current phase
        status = self.controller.get_status()
        phase_timings = status['phase_timings']
        current_phase = self.controller.current_phase
        
        # Initialize all directions with 0
        for direction in ['north', 'south', 'east', 'west']:
            self.history['green_times'][direction].append(0)
        
        # Set green time for current green direction
        if current_phase.value == 'N_GREEN':
            self.history['green_times']['north'][-1] = phase_timings.get('N_GREEN', 0)
        elif current_phase.value == 'S_GREEN':
            self.history['green_times']['south'][-1] = phase_timings.get('S_GREEN', 0)
        elif current_phase.value == 'E_GREEN':
            self.history['green_times']['east'][-1] = phase_timings.get('E_GREEN', 0)
        elif current_phase.value == 'W_GREEN':
            self.history['green_times']['west'][-1] = phase_timings.get('W_GREEN', 0)
        
        # Record pressures
        pressures = status['pressures']
        for direction in ['north', 'south', 'east', 'west']:
            self.history['pressures'][direction].append(pressures[direction])
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_intersection(self, result: dict):
        """Display ASCII visualization of the intersection"""
        phase = result['phase']
        queues = result['queues']
        green_dir = result['green_direction']
        remaining = self.controller.get_remaining_time()
        
        # Get status for metrics
        status = self.controller.get_status()
        
        self.clear_screen()
        
        print("=" * 80)
        print(" " * 20 + "ADVANCED TRAFFIC SIMULATION")
        print(" " * 15 + "(Individual Direction Control)")
        print("=" * 80)
        print()
        
        # Determine light colors for each direction
        light_colors = {}
        for direction in ['north', 'south', 'east', 'west']:
            if direction == green_dir:
                light_colors[direction] = 'G'  # Green
            elif (direction == 'north' and phase.value in ['N_YELLOW', 'ALL_RED']) or \
                 (direction == 'south' and phase.value in ['S_YELLOW', 'ALL_RED']) or \
                 (direction == 'east' and phase.value in ['E_YELLOW', 'ALL_RED']) or \
                 (direction == 'west' and phase.value in ['W_YELLOW', 'ALL_RED']):
                light_colors[direction] = 'Y'  # Yellow
            else:
                light_colors[direction] = 'R'  # Red
        
        # North display
        print(f"        NORTH: {queues['north']:3d} vehicles")
        print(f"        Light: [{light_colors['north']}] {phase.value}")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {light_colors['north']}   |")
        print("           |   v   |")
        print("           +-------+")
        print()
        
        # West-East display
        print(f"  WEST: {queues['west']:3d} vehicles                EAST: {queues['east']:3d} vehicles")
        print(f"  Light: [{light_colors.get('west', 'R')}]                      Light: [{light_colors.get('east', 'R')}]")
        print()
        print("           +-------+")
        print("           |  <    |")
        print(f"           |   {light_colors.get('west', 'R')}   |")
        print("           |   >   |")
        print("           +-------+")
        print()
        
        # South display
        print(f"        SOUTH: {queues['south']:3d} vehicles          Light: [{light_colors.get('south', 'R')}]")
        print()
        print("           +-------+")
        print("           |   ^   |")
        print(f"           |   {light_colors.get('south', 'R')}   |")
        print("           |   v   |")
        print("           +-------+")
        print()
        
        # Current phase and timing
        print("=" * 80)
        print(f"Current Phase: {phase.value:15s} | Remaining: {remaining:5.1f}s")
        print(f"Green Direction: {green_dir if green_dir else 'None':10s} | Vehicles discharged: {result['vehicles_discharged']:3d}")
        print()
        
        # Direction-specific information
        print("Direction    Queue    Pressure    Green Time    Processed")
        print("-" * 60)
        for direction in ['north', 'south', 'east', 'west']:
            pressure = status['pressures'][direction]
            green_time = status['phase_timings'].get(f'{direction[0].upper()}_GREEN', 0)
            processed = status['performance']['direction_processed'][direction]
            
            print(f"{direction:10s} {queues[direction]:6d} {pressure:10.1f} {green_time:12.1f}s {processed:12d}")
        
        print()
        
        # Performance metrics
        print("Performance Metrics:")
        print(f"Efficiency: {status['performance']['efficiency']:5.1f}% | Throughput: {status['performance']['throughput']:5.1f} veh/min")
        print(f"Total processed: {status['performance']['vehicles_processed']:5d} vehicles")
        print("=" * 80)
    
    def print_step_summary(self, step: int, result: dict):
        """Print a one-line summary for the current step"""
        phase = result['phase'].value
        queues = result['queues']
        green_dir = result['green_direction'] or "None"
        discharged = result['vehicles_discharged']
        
        # Get pressures
        pressures = result['pressures']
        
        print(f"Step {step:3d} | Phase: {phase:10s} | Green: {green_dir:5s} | "
              f"N:{queues['north']:3d}({pressures['north']:4.1f}) "
              f"S:{queues['south']:3d}({pressures['south']:4.1f}) "
              f"E:{queues['east']:3d}({pressures['east']:4.1f}) "
              f"W:{queues['west']:3d}({pressures['west']:4.1f}) | "
              f"Discharged: {discharged:2d}")
    
    def run(self, steps: int = 200, delay: float = 0.2, display: bool = True):
        """Run the simulation for specified number of steps"""
        print("=" * 80)
        print("Starting Advanced Traffic Simulation")
        print("Each direction (N, S, E, W) has individual timing control")
        print("=" * 80)
        print()
        
        try:
            for step in range(1, steps + 1):
                result = self.update(delta_time=1.0)
                
                if display:
                    self.display_intersection(result)
                    time.sleep(delay)
                else:
                    # Print summary every 10 steps
                    if step % 10 == 0 or step == 1:
                        self.print_step_summary(step, result)
                
                # Check for excessive queue buildup
                max_queue = max(self.queues.values())
                if max_queue > 50:
                    print(f"\nWarning: Queue buildup detected (max: {max_queue} vehicles)")
        
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user.")
        
        finally:
            self.print_final_summary()
    
    def print_final_summary(self):
        """Print final simulation summary"""
        print("\n" + "=" * 80)
        print("SIMULATION SUMMARY")
        print("=" * 80)
        
        total_steps = len(self.history['timestamps'])
        if total_steps == 0:
            print("No data collected.")
            return
        
        # Get final status
        status = self.controller.get_status()
        
        print(f"Total simulation steps: {total_steps}")
        print(f"Total simulation time: {total_steps} seconds")
        print()
        
        print("Final Queue Status:")
        for direction in ['north', 'south', 'east', 'west']:
            print(f"  {direction.capitalize()}: {self.queues[direction]:3d} vehicles")
        
        print()
        print("Performance Metrics:")
        print(f"  Efficiency: {status['performance']['efficiency']:5.1f}%")
        print(f"  Throughput: {status['performance']['throughput']:5.1f} vehicles/min")
        print(f"  Total vehicles processed: {status['performance']['vehicles_processed']:5d}")
        
        print()
        print("Direction Processing Summary:")
        for direction in ['north', 'south', 'east', 'west']:
            processed = status['performance']['direction_processed'][direction]
            print(f"  {direction.capitalize()}: {processed:5d} vehicles")
        
        print()
        print("Average Queue Lengths:")
        for direction in ['north', 'south', 'east', 'west']:
            avg_queue = sum(self.history['queues'][direction]) / total_steps
            print(f"  {direction.capitalize()}: {avg_queue:5.1f} vehicles")
        
        print("=" * 80)


def main():
    """Main entry point for advanced simulation"""
    # Create configuration
    config = AdvancedTrafficConfig(
        min_green_time=10.0,    # Slightly higher minimum for stability
        max_green_time=60.0,    # Higher maximum to handle heavy traffic
        yellow_time=3.0,
        all_red_time=2.0,
        vehicle_threshold=3,
        extension_per_vehicle=0.7,
        max_extension=25.0,     # Higher extension cap
        gap_time=2.0,
        min_phase_cycle=2,
        pressure_threshold=1.3
    )
    
    # Create and run simulation
    sim = AdvancedTrafficSimulator(config)
    
    print("Advanced Traffic Light Simulation")
    print("=================================")
    print("This simulation treats each direction (N, S, E, W) separately.")
    print("The algorithm uses max-pressure control to decide which direction gets green.")
    print()
    print("Press Ctrl+C to stop the simulation.")
    print()
    
    try:
        # Run for 150 steps (2.5 minutes simulation time)
        sim.run(steps=150, delay=0.15, display=True)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")


if __name__ == "__main__":
    main()