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
        
        # Data storage - Basic metrics
        self.timestamps = []
        self.queue_north = []
        self.queue_south = []
        self.queue_east = []
        self.queue_west = []
        self.throughput = []
        self.phases = []
        
        # Additional metrics for deeper analysis
        self.total_queue = []          # Sum of all queues
        self.ns_total = []             # North-South combined queue
        self.ew_total = []             # East-West combined queue
        self.queue_balance = []        # Difference between NS and EW totals
        self.green_times_ns = []       # NS green duration when allocated
        self.green_times_ew = []       # EW green duration when allocated
        self.pressure_ns = []          # Pressure metric for NS
        self.pressure_ew = []          # Pressure metric for EW
        self.cumulative_throughput = []  # Cumulative vehicles processed
        self.arrival_rates = []        # Track arrival rate changes
        
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
        """Initialize the six subplots"""
        # Create 6 subplots (3x2 grid)
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4), (self.ax5, self.ax6)) = plt.subplots(3, 2, figsize=(14, 10))
        self.fig.suptitle('Traffic Simulation Real-Time Visualization', fontsize=14, fontweight='bold')
        
        # Plot 1: Queue lengths
        self.ax1.set_title('Queue Lengths Over Time')
        self.ax1.set_ylabel('Vehicles')
        self.ax1.set_xlabel('Time Step')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot 2: Total Congestion
        self.ax2.set_title('Total Queue Congestion')
        self.ax2.set_ylabel('Total Vehicles')
        self.ax2.set_xlabel('Time Step')
        self.ax2.grid(True, alpha=0.3)
        
        # Plot 3: Throughput
        self.ax3.set_title('Vehicle Throughput')
        self.ax3.set_ylabel('Vehicles/min')
        self.ax3.set_xlabel('Time Step')
        self.ax3.grid(True, alpha=0.3)
        
        # Plot 4: Queue Balance (NS vs EW)
        self.ax4.set_title('Queue Balance (NS - EW)')
        self.ax4.set_ylabel('Difference')
        self.ax4.set_xlabel('Time Step')
        self.ax4.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        self.ax4.grid(True, alpha=0.3)
        
        # Plot 5: Green Time Durations
        self.ax5.set_title('Green Time Durations')
        self.ax5.set_ylabel('Seconds')
        self.ax5.set_xlabel('Time Step')
        self.ax5.grid(True, alpha=0.3)
        
        # Plot 6: Pressure Metrics
        self.ax6.set_title('Traffic Pressure (Queue × Arrival Rate)')
        self.ax6.set_ylabel('Pressure Index')
        self.ax6.set_xlabel('Time Step')
        self.ax6.grid(True, alpha=0.3)
        
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
        
        # Calculate additional metrics
        ns_sum = queues['north'] + queues['south']
        ew_sum = queues['east'] + queues['west']
        total = ns_sum + ew_sum
        balance = ns_sum - ew_sum
        
        self.total_queue.append(total)
        self.ns_total.append(ns_sum)
        self.ew_total.append(ew_sum)
        self.queue_balance.append(balance)
        
        # Track green times (store the allocated time for current green phase)
        phase_timings = status['phase_timings']
        current_phase_str = status['current_phase'].value if hasattr(status['current_phase'], 'value') else str(status['current_phase'])
        if current_phase_str == 'NS_GREEN':
            self.green_times_ns.append(phase_timings.get('NS_GREEN', 0))
            self.green_times_ew.append(np.nan)
        elif current_phase_str == 'EW_GREEN':
            self.green_times_ew.append(phase_timings.get('EW_GREEN', 0))
            self.green_times_ns.append(np.nan)
        else:
            self.green_times_ns.append(np.nan)
            self.green_times_ew.append(np.nan)
        
        # Calculate pressure metrics (queue * arrival rate)
        # Access arrival rates from controller
        controller = self.simulator.controller
        ns_pressure = (queues['north'] + queues['south']) * (
            (controller.arrival_rates['north'] + controller.arrival_rates['south']) / 2
        )
        ew_pressure = (queues['east'] + queues['west']) * (
            (controller.arrival_rates['east'] + controller.arrival_rates['west']) / 2
        )
        self.pressure_ns.append(ns_pressure)
        self.pressure_ew.append(ew_pressure)
        
        # Track cumulative throughput
        if not self.cumulative_throughput:
            self.cumulative_throughput.append(controller.total_vehicles_processed)
        else:
            self.cumulative_throughput.append(controller.total_vehicles_processed)
        
        # Track arrival rate (average of all directions)
        avg_arrival = np.mean([
            controller.arrival_rates['north'],
            controller.arrival_rates['south'],
            controller.arrival_rates['east'],
            controller.arrival_rates['west']
        ])
        self.arrival_rates.append(avg_arrival)
        
        # Keep only last max_points
        if len(self.timestamps) > self.max_points:
            self.timestamps = self.timestamps[-self.max_points:]
            self.queue_north = self.queue_north[-self.max_points:]
            self.queue_south = self.queue_south[-self.max_points:]
            self.queue_east = self.queue_east[-self.max_points:]
            self.queue_west = self.queue_west[-self.max_points:]
            self.throughput = self.throughput[-self.max_points:]
            self.phases = self.phases[-self.max_points:]
            self.total_queue = self.total_queue[-self.max_points:]
            self.ns_total = self.ns_total[-self.max_points:]
            self.ew_total = self.ew_total[-self.max_points:]
            self.queue_balance = self.queue_balance[-self.max_points:]
            self.green_times_ns = self.green_times_ns[-self.max_points:]
            self.green_times_ew = self.green_times_ew[-self.max_points:]
            self.pressure_ns = self.pressure_ns[-self.max_points:]
            self.pressure_ew = self.pressure_ew[-self.max_points:]
            self.cumulative_throughput = self.cumulative_throughput[-self.max_points:]
            self.arrival_rates = self.arrival_rates[-self.max_points:]
        
        # Clear and redraw all plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.ax5.clear()
        self.ax6.clear()
        
        # Plot 1: Queue lengths
        self.ax1.plot(self.timestamps, self.queue_north, 'r-', label='North', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_south, 'b-', label='South', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_east, 'g-', label='East', linewidth=2)
        self.ax1.plot(self.timestamps, self.queue_west, 'm-', label='West', linewidth=2)
        self.ax1.set_title('Queue Lengths Over Time')
        self.ax1.set_ylabel('Vehicles')
        self.ax1.set_xlabel('Time Step')
        self.ax1.legend(loc='upper left')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot 2: Total Congestion
        self.ax2.plot(self.timestamps, self.total_queue, 'k-', linewidth=2, label='Total')
        self.ax2.fill_between(self.timestamps, self.total_queue, alpha=0.3, color='gray')
        self.ax2.plot(self.timestamps, self.ns_total, 'r--', linewidth=1.5, label='NS Total', alpha=0.7)
        self.ax2.plot(self.timestamps, self.ew_total, 'b--', linewidth=1.5, label='EW Total', alpha=0.7)
        self.ax2.set_title('Total Queue Congestion')
        self.ax2.set_ylabel('Total Vehicles')
        self.ax2.set_xlabel('Time Step')
        self.ax2.legend(loc='upper left')
        self.ax2.grid(True, alpha=0.3)
        
        # Plot 3: Throughput
        self.ax3.plot(self.timestamps, self.throughput, 'k-', linewidth=2)
        self.ax3.fill_between(self.timestamps, self.throughput, alpha=0.3)
        self.ax3.set_title('Vehicle Throughput')
        self.ax3.set_ylabel('Vehicles/min')
        self.ax3.set_xlabel('Time Step')
        self.ax3.grid(True, alpha=0.3)
        
        # Plot 4: Queue Balance
        self.ax4.plot(self.timestamps, self.queue_balance, 'purple', linewidth=2)
        self.ax4.fill_between(self.timestamps, self.queue_balance, alpha=0.3, color='purple')
        self.ax4.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        self.ax4.set_title('Queue Balance (NS - EW)')
        self.ax4.set_ylabel('Difference')
        self.ax4.set_xlabel('Time Step')
        self.ax4.grid(True, alpha=0.3)
        
        # Plot 5: Green Time Durations
        # Use scatter for points where green is active
        ns_x = [self.timestamps[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ns[i])]
        ns_y = [self.green_times_ns[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ns[i])]
        ew_x = [self.timestamps[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ew[i])]
        ew_y = [self.green_times_ew[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ew[i])]
        
        self.ax5.scatter(ns_x, ns_y, c='green', label='NS Green', s=30, alpha=0.7)
        self.ax5.scatter(ew_x, ew_y, c='blue', label='EW Green', s=30, alpha=0.7)
        self.ax5.set_title('Green Time Durations')
        self.ax5.set_ylabel('Seconds')
        self.ax5.set_xlabel('Time Step')
        self.ax5.legend(loc='upper left')
        self.ax5.grid(True, alpha=0.3)
        
        # Plot 6: Pressure Metrics
        self.ax6.plot(self.timestamps, self.pressure_ns, 'g-', linewidth=2, label='NS Pressure', alpha=0.8)
        self.ax6.plot(self.timestamps, self.pressure_ew, 'orange', linewidth=2, label='EW Pressure', alpha=0.8)
        self.ax6.fill_between(self.timestamps, self.pressure_ns, alpha=0.2, color='green')
        self.ax6.fill_between(self.timestamps, self.pressure_ew, alpha=0.2, color='orange')
        self.ax6.set_title('Traffic Pressure (Queue × Arrival Rate)')
        self.ax6.set_ylabel('Pressure Index')
        self.ax6.set_xlabel('Time Step')
        self.ax6.legend(loc='upper left')
        self.ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.pause(0.001)
        
    def final_plot(self):
        """Create final static plots after simulation ends"""
        plt.ioff()
        
        # Figure 1: 6 metric plots
        self.fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 12))
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
        
        # Plot 2: Total Congestion
        ax2.plot(self.timestamps, self.total_queue, 'k-', linewidth=2, label='Total')
        ax2.fill_between(self.timestamps, self.total_queue, alpha=0.3, color='gray')
        ax2.plot(self.timestamps, self.ns_total, 'r--', linewidth=1.5, label='NS Total', alpha=0.7)
        ax2.plot(self.timestamps, self.ew_total, 'b--', linewidth=1.5, label='EW Total', alpha=0.7)
        ax2.set_title('Total Queue Congestion')
        ax2.set_ylabel('Total Vehicles')
        ax2.set_xlabel('Time Step')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Throughput
        ax3.plot(self.timestamps, self.throughput, 'k-', linewidth=2)
        ax3.fill_between(self.timestamps, self.throughput, alpha=0.3, color='gray')
        ax3.axhline(y=np.mean(self.throughput), color='r', linestyle='--', 
                   label=f'Average: {np.mean(self.throughput):.1f}')
        ax3.set_title('Vehicle Throughput')
        ax3.set_ylabel('Vehicles/min')
        ax3.set_xlabel('Time Step')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 3b: Cumulative Throughput (on same axes, right side)
        ax3_twin = ax3.twinx()
        ax3_twin.plot(self.timestamps, self.cumulative_throughput, 'darkgreen', linewidth=2, 
                     label='Cumulative', alpha=0.6)
        ax3_twin.set_ylabel('Total Vehicles Processed', color='darkgreen')
        ax3_twin.tick_params(axis='y', labelcolor='darkgreen')
        # Combine legends
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Plot 4: Queue Balance
        ax4.plot(self.timestamps, self.queue_balance, 'purple', linewidth=2)
        ax4.fill_between(self.timestamps, self.queue_balance, alpha=0.3, color='purple')
        ax4.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        ax4.set_title('Queue Balance (NS - EW)')
        ax4.set_ylabel('Difference')
        ax4.set_xlabel('Time Step')
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Green Time Durations
        ns_x = [self.timestamps[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ns[i])]
        ns_y = [self.green_times_ns[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ns[i])]
        ew_x = [self.timestamps[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ew[i])]
        ew_y = [self.green_times_ew[i] for i in range(len(self.timestamps)) if not np.isnan(self.green_times_ew[i])]
        
        ax5.scatter(ns_x, ns_y, c='green', label='NS Green', s=30, alpha=0.7)
        ax5.scatter(ew_x, ew_y, c='blue', label='EW Green', s=30, alpha=0.7)
        ax5.set_title('Green Time Durations')
        ax5.set_ylabel('Seconds')
        ax5.set_xlabel('Time Step')
        ax5.legend(loc='upper left')
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Pressure Metrics
        ax6.plot(self.timestamps, self.pressure_ns, 'g-', linewidth=2, label='NS Pressure', alpha=0.8)
        ax6.plot(self.timestamps, self.pressure_ew, 'orange', linewidth=2, label='EW Pressure', alpha=0.8)
        ax6.fill_between(self.timestamps, self.pressure_ns, alpha=0.2, color='green')
        ax6.fill_between(self.timestamps, self.pressure_ew, alpha=0.2, color='orange')
        ax6.set_title('Traffic Pressure (Queue × Arrival Rate)')
        ax6.set_ylabel('Pressure Index')
        ax6.set_xlabel('Time Step')
        ax6.legend(loc='upper left')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Figure 2: Phase timeline
        fig2, ax_phase = plt.subplots(1, 1, figsize=(14, 3))
        fig2.suptitle('Traffic Light Phase Timeline', fontsize=12, fontweight='bold')
        
        # Plot phase timeline with colored bars
        for i, phase in enumerate(self.phases):
            phase_key = phase.value if hasattr(phase, 'value') else str(phase)
            color = self.phase_colors.get(phase_key, 'gray')
            ax_phase.axvspan(self.timestamps[i] - 0.5, self.timestamps[i] + 0.5, 
                        color=color, alpha=0.7, ec='none')
        ax_phase.set_title('Phase Transitions')
        ax_phase.set_ylabel('Phase')
        ax_phase.set_xlabel('Time Step')
        ax_phase.set_yticks([])
        ax_phase.grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, alpha=0.7, label=phase) 
                          for phase, color in self.phase_colors.items()]
        ax_phase.legend(handles=legend_elements, loc='upper left')
        
        plt.tight_layout()
        
        # Add summary statistics text box
        summary_text = self._generate_summary_text()
        self.fig.text(0.02, 0.02, summary_text, fontsize=9,
                     bbox=dict(boxstyle="round,pad=0.5", facecolor="wheat", alpha=0.8),
                     verticalalignment='bottom')
        
        plt.show()
    
    def _generate_summary_text(self) -> str:
        """Generate summary statistics text for final plot"""
        if not self.timestamps:
            return "No data available"
        
        # Calculate statistics
        avg_throughput = np.mean(self.throughput)
        max_throughput = np.max(self.throughput)
        avg_total_queue = np.mean(self.total_queue)
        max_total_queue = np.max(self.total_queue)
        avg_ns_queue = np.mean(self.ns_total)
        avg_ew_queue = np.mean(self.ew_total)
        
        # Average green times (excluding NaN)
        ns_green_vals = [x for x in self.green_times_ns if not np.isnan(x)]
        ew_green_vals = [x for x in self.green_times_ew if not np.isnan(x)]
        avg_ns_green = np.mean(ns_green_vals) if ns_green_vals else 0
        avg_ew_green = np.mean(ew_green_vals) if ew_green_vals else 0
        
        # Pressure statistics
        avg_ns_pressure = np.mean(self.pressure_ns)
        avg_ew_pressure = np.mean(self.pressure_ew)
        
        # Phase counts
        ns_green_count = len(ns_green_vals)
        ew_green_count = len(ew_green_vals)
        
        # Build summary string
        summary = "SUMMARY STATISTICS:\n"
        summary += f"Throughput: Avg={avg_throughput:.1f} veh/min, Peak={max_throughput:.1f}\n"
        summary += f"Queues: Avg Total={avg_total_queue:.1f}, Max Total={max_total_queue:.1f}\n"
        summary += f"Queue Split: NS={avg_ns_queue:.1f}, EW={avg_ew_queue:.1f}\n"
        summary += f"Green Times: NS={avg_ns_green:.1f}s ({ns_green_count} phases), EW={avg_ew_green:.1f}s ({ew_green_count} phases)\n"
        summary += f"Pressure: NS={avg_ns_pressure:.1f}, EW={avg_ew_pressure:.1f}\n"
        summary += f"Total Vehicles Processed: {self.cumulative_throughput[-1] if self.cumulative_throughput else 0}"
        
        return summary


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
