"""
Enhanced Traffic Light Configuration with Advanced Parameters
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class EnhancedTrafficLightConfig:
    """Advanced configuration for smart traffic light controller"""
    
    # Core timing parameters
    min_green_time: float = 12.0      # Minimum green time in seconds
    max_green_time: float = 60.0      # Maximum green time in seconds (increased for high throughput)
    yellow_time: float = 3.5         # Yellow light duration
    all_red_time: float = 2.0        # All-red clearance interval
    
    # Adaptive timing parameters
    vehicle_threshold: int = 4        # Minimum vehicles to consider extension
    extension_per_vehicle: float = 0.6  # Seconds added per vehicle
    max_extension: float = 18.0      # Maximum extension beyond base time
    
    # Gap time parameters (new feature)
    gap_time: float = 2.5            # Gap between last vehicle and phase end (seconds)
    min_gap_time: float = 1.0        # Minimum gap time regardless of vehicle count
    
    # Traffic pattern parameters
    arrival_rate: float = 1.2        # Base arrival rate (vehicles/second) - higher throughput
    saturation_flow: float = 3.2     # Vehicles discharged per second when green
    
    # Performance optimization
    max_queue_length: int = 20       # Maximum queue length before priority boost
    priority_boost: float = 1.3      # Multiplier for high-traffic directions
    
    # Safety parameters
    emergency_vehicle_detection: bool = True  # Enable emergency vehicle priority
    emergency_priority_time: float = 30.0     # Extended green for emergency vehicles
    
    def get_config(self) -> dict:
        """Get configuration as dictionary"""
        return {
            'min_green_time': self.min_green_time,
            'max_green_time': self.max_green_time,
            'yellow_time': self.yellow_time,
            'all_red_time': self.all_red_time,
            'vehicle_threshold': self.vehicle_threshold,
            'extension_per_vehicle': self.extension_per_vehicle,
            'max_extension': self.max_extension,
            'gap_time': self.gap_time,
            'min_gap_time': self.min_gap_time,
            'arrival_rate': self.arrival_rate,
            'saturation_flow': self.saturation_flow,
            'max_queue_length': self.max_queue_length,
            'priority_boost': self.priority_boost,
            'emergency_vehicle_detection': self.emergency_vehicle_detection,
            'emergency_priority_time': self.emergency_priority_time
        }