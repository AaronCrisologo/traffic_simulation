"""
Traffic Simulation Visualizer
Creates real-time and post-simulation visualizations of traffic data
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import numpy as np
from collections import deque
from simple_simulation import SimpleTrafficSimulator
from enhanced_config import EnhancedTrafficLightConfig


class TrafficVisualizer:
    """Real-time visualization for traffic simulation"""
    
    def __init__(self, simulator, max_points=200):
        self.simulator = simulator
        self.max_points = max_points
        
        # Data storage
        self.timestamps = []
        self.queue_north = []
        self.queue_south = []
        self.queue_east = []
        self.queue_west = []
        self.throughput = []
        self.phases = []
        
        # Phase colors for plotting
        self.phase_colors = {
            'NS_GREEN': 'green',
            'EW_GREEN': 'blue',
            'NS_YELLOW': 'yellow',
            'EW_YELLOW': 'orange',
            'ALL_RED': 'red'
        }
        
        # Setup figure
        plt.ion()  # Interactive mode
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 8))
        self.fig.suptitle('Traffic Simulation Real-Time Visualization', fontsize=14, fontweight='bold')
        
        # Initialize plots
        self.setup_plots()
        
    def setup_plots(self):
        """Initialize the three subplots"""
        # Plot 1: Queue lengths
        self.ax1.set_title('Queue Lengths Over Time')
        self.ax1.set_ylabel('Vehicles')
        self.ax1.set_xlabel('Time Step')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot 2: Throughput
        self.ax2.set_title('Vehicle Throughput')
        self.ax2.set_ylabel('Vehicles/min')
        self.ax2.set_xlabel('Time Step')
        self.ax2.grid(True, alpha=0.3)
        
        # Plot 3: Phase timeline
        self.ax3.set_title('Traffic Light Phases')
        self.ax3.set_ylabel('Phase')
        self.ax3.set_xlabel('Time Step')
        self.ax3.set_yticks(range(len(self.phase_colors)))
        self.ax3.set_yticklabels(self.phase_colors.keys(), fontsize=8)
        self.ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
    def update(self, step, result, status):
        """Update visualization with new data point"""
        # Store data
        self.timestamps.append(step)
        queues = result['queues']
        self.queue_north.append(queues['north'])
        self.queue_south.append(queues['south'])
        self.queue_east.append(queues['east'])
        self.queue_west.append(queues['west'])
        self.throughput.append(status['performance']['vehicle_throughput'])
        self.phases.append(status['current_phase'])
        
        # Keep only last max_points
        if len(self.timestamps) > self.max_points:
            self.timestamps = self.timestamps[-self.max_points:]
            self.queue_north = self.queue_north[-self.max_points:]
            self.queue_south = self.queue_south[-self.max_points:]
            self.queue_east = self.queue_east[-self.max_points:]
            self.queue_west = self.queue_west[-self.max_points:]
            self.throughput = self.throughput[-self.max_points:]
            self.phases = self.phases[-self.max_points:]
        
        # Clear and redraw
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Plot queues
        self.ax1.plot(self.timestamps, self.queue_north, 'r-', label='North', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_south, 'b-', label='South', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_east, 'g-', label='East', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_west, 'm-', label='West', linewidth=2)
        self.ax1.set_title('Queue Lengths Over Time')
        self.ax1.set_ylabel('Vehicles')
        self.ax1.set_xlabel('Time Step')
        self.ax1.legend(loc='upper left')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot throughput
        self.ax2.plot(self.timestamps, self.throughput, 'k-', linewidth=2)
        self.ax2.fill_between(self.timestamps, self.throughput, alpha=0.3)
        self.ax2.set_title('Vehicle Throughput')
        self.ax2.set_ylabel('Vehicles/min')
        self.ax2.set_xlabel('Time Step')
        self.ax2.grid(True, alpha=0.3)
        
        # Plot phases as colored background regions
        for i, phase in enumerate(self.phases):
            # Handle both enum and string phases
            phase_key = phase.value if hasattr(phase, 'value') else str(phase)
            color = self.phase_colors.get(phase_key, 'gray')
            self.ax3.axvspan(self.timestamps[i] - 0.5, self.timestamps[i] + 0.5, 
                            color=color, alpha=0.5, ec='none')
        self.ax3.set_title('Traffic Light Phases')
        self.ax3.set_ylabel('Phase')
        self.ax3.set_xlabel('Time Step')
        self.ax3.set_yticks([])
        self.ax3.grid(True, alpha=0.3)
        
        # Add legend for phases
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, alpha=0.5, label=phase) 
                          for phase, color in self.phase_colors.items()]
        self.ax3.legend(handles=legend_elements, loc='upper left', fontsize=8)
        
        plt.tight_layout()
        plt.pause(0.001)
        
    def final_plot(self):
        """Create final static plots after simulation ends"""
        plt.ioff()
        self.fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        self.fig.suptitle('Traffic Simulation Results - Final Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Queue lengths
        ax1.plot(self.timestamps, self.queue_north, 'r-', label='North', linewidth=2)
        ax1.plot(self.timestamps, self.queue_south, 'b-', label='South', linewidth=2)
        ax1.plot(self.timestamps, self.queue_east, 'g-', label='East', linewidth=2)
        ax1.plot(self.timestamps, self.queue_west, 'm-', label='West', linewidth=2)
        ax1.set_title('Queue Lengths Over Time')
        ax1.set_ylabel('Vehicles')
        ax1.set_xlabel('Time Step')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Throughput
        ax2.plot(self.timestamps, self.throughput, 'k-', linewidth=2)
        ax2.fill_between(self.timestamps, self.throughput, alpha=0.3, color='gray')
        ax2.set_title('Vehicle Throughput')
        ax2.set_ylabel('Vehicles/min')
        ax2.set_xlabel('Time Step')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=np.mean(self.throughput), color='r', linestyle='--', 
                   label=f'Average: {np.mean(self.throughput):.1f}')
        ax2.legend()
        
        # Plot 3: Phase timeline with colored bars
        for i, phase in enumerate(self.phases):
            # Handle both enum and string phases
            phase_key = phase.value if hasattr(phase, 'value') else str(phase)
            color = self.phase_colors.get(phase_key, 'gray')
            ax3.axvspan(self.timestamps[i] - 0.5, self.timestamps[i] + 0.5, 
                        color=color, alpha=0.7, ec='none')
        ax3.set_title('Traffic Light Phases Timeline')
        ax3.set_ylabel('Phase')
        ax3.set_xlabel('Time Step')
        ax3.set_yticks([])
        ax3.grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, alpha=0.7, label=phase) 
                          for phase, color in self.phase_colors.items()]
        ax3.legend(handles=legend_elements, loc='upper left')
        
        plt.tight_layout()
        plt.show()


def run_visualization():
    """Run simulation with real-time visualization"""
    config = EnhancedTrafficLightConfig(
        min_green_time=12.0,
        max_green_time=60.0,
        yellow_time=3.5,
        all_red_time=2.0,
        vehicle_threshold=4,
        extension_per_vehicle=0.6,
        max_extension=15.0,
        gap_time=2.5,
        arrival_rate=1.0,      # Base arrival rate
        saturation_flow=2.5,   # Discharge capacity
    )
    
    sim = SimpleTrafficSimulator(config)
    visualizer = TrafficVisualizer(sim, max_points=100)
    
    print("=" * 100)
    print("RUNNING SIMULATION WITH REAL-TIME VISUALIZATION")
    print("=" * 100)
    print("Close the plot window to stop the simulation early.")
    print()
    
    try:
        for i in range(200):
            # Dynamic arrival rate
            base_rate = 1.0
            cycle_position = i % 120
            if cycle_position < 30:
                cycle_multiplier = 1.3
            elif cycle_position < 90:
                cycle_multiplier = 1.0
            else:
                cycle_multiplier = 1.2
            
            random_factor = np.random.uniform(0.85, 1.15)
            spike = 1.4 if np.random.random() < 0.05 else 1.0
            dynamic_rate = base_rate * cycle_multiplier * random_factor * spike
            sim.arrival_rate = dynamic_rate
            
            # Update simulation
            result = sim.update(delta_time=1.0)
            status = sim.controller.get_status()
            
            # Update visualization
            visualizer.update(i + 1, result, status)
            
            # Print summary every 20 steps
            if (i + 1) % 20 == 0:
                queues = result['queues']
                phase_str = status['current_phase'].value if hasattr(status['current_phase'], 'value') else str(status['current_phase'])
                print(f"Step {i+1:3d} | Phase: {phase_str:15s} | "
                      f"N:{queues['north']:3d} S:{queues['south']:3d} "
                      f"E:{queues['east']:3d} W:{queues['west']:3d} | "
                      f"Throughput: {status['performance']['vehicle_throughput']:6.1f}")
            
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    
    print("\n" + "=" * 100)
    print("SIMULATION COMPLETE")
    print("=" * 100)
    print(f"Total steps: {len(visualizer.timestamps)}")
    print(f"Final queues: N={visualizer.queue_north[-1]}, "
          f"S={visualizer.queue_south[-1]}, "
          f"E={visualizer.queue_east[-1]}, "
          f"W={visualizer.queue_west[-1]}")
    print(f"Average throughput: {np.mean(visualizer.throughput):.1f} vehicles/min")
    print("=" * 100)
    
    # Show final static plots
    visualizer.final_plot()


if __name__ == "__main__":
    run_visualization()
