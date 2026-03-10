"""
Traffic Light Controller with Adaptive Timing Algorithm
Adjusts signal timing based on vehicle counts from CNN detection
"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class LightPhase(Enum):
    """Traffic light phases for a 4-way intersection"""
    NORTH_SOUTH_GREEN = "NS_GREEN"
    NORTH_SOUTH_YELLOW = "NS_YELLOW"
    EAST_WEST_GREEN = "EW_GREEN"
    EAST_WEST_YELLOW = "EW_YELLOW"
    ALL_RED = "ALL_RED"


@dataclass
class TrafficLightConfig:
    """Configuration for traffic light timing"""
    min_green_time: float = 15.0  # Minimum green time in seconds
    max_green_time: float = 60.0  # Maximum green time in seconds
    yellow_time: float = 4.0  # Yellow light duration
    all_red_time: float = 2.0  # All-red clearance interval
    vehicle_threshold: int = 5   # Minimum vehicles to consider extension
    extension_per_vehicle: float = 0.5  # Seconds added per vehicle
    max_extension: float = 20.0  # Maximum extension beyond base time
    gap_time: float = 3.0  # Gap between last vehicle and phase end (seconds)


class TrafficLightController:
    """
    Smart traffic light controller that adjusts timing based on vehicle detection.
    Designed to integrate with CNN model output from 4 cameras.
    """
    
    def __init__(self, config: TrafficLightConfig = None):
        self.config = config or TrafficLightConfig()
        self.current_phase = LightPhase.NORTH_SOUTH_GREEN
        self.current_phase_elapsed = 0.0  # Simulation time in current phase
        self.vehicle_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        self.phase_timings = {
            LightPhase.NORTH_SOUTH_GREEN: self._calculate_green_time('north', 'south'),
            LightPhase.NORTH_SOUTH_YELLOW: self.config.yellow_time,
            LightPhase.EAST_WEST_GREEN: self._calculate_green_time('east', 'west'),
            LightPhase.EAST_WEST_YELLOW: self.config.yellow_time,
            LightPhase.ALL_RED: self.config.all_red_time
        }
        # Track actual phase durations for analysis
        self.actual_phase_durations = []
        
    def update_vehicle_counts(self, north: int, south: int, east: int, west: int):
        """Update vehicle counts from CNN detection (4 cameras)"""
        self.vehicle_counts['north'] = north
        self.vehicle_counts['south'] = south
        self.vehicle_counts['east'] = east
        self.vehicle_counts['west'] = west
        
        # Recalculate green times based on new counts
        self._recalculate_timings()
    
    def _calculate_green_time(self, dir1: str, dir2: str) -> float:
        """Calculate adaptive green time based on vehicle counts with gap time consideration."""
        total_vehicles = self.vehicle_counts[dir1] + self.vehicle_counts[dir2]

        if total_vehicles <= 0:
            return self.config.min_green_time

        # Base time plus extension based on vehicle count
        base_time = self.config.min_green_time
        extension = min(total_vehicles * self.config.extension_per_vehicle,
                       self.config.max_extension)

        # Add gap time for vehicle clearance
        gap_time = self.config.gap_time * total_vehicles

        adaptive_time = base_time + extension + gap_time

        # Clamp to min/max bounds
        return max(self.config.min_green_time,
                  min(adaptive_time, self.config.max_green_time))
    
    def update(self, delta_time: float = 1.0) -> LightPhase:
        """
        Update traffic light state based on elapsed time.
        Returns the new phase if changed, otherwise current phase.
        """
        # Advance time in current phase
        self.current_phase_elapsed += delta_time

        current_duration = self.phase_timings[self.current_phase]

        # Check if we should extend the current green phase
        if self.current_phase in (LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN):
            extension = self.get_extension_time()
            if extension > 0:
                current_duration += extension

        # Check if phase should transition (fixed logic)
        if self.current_phase_elapsed >= current_duration:
            # Record actual duration of this phase before transitioning
            actual_duration = self.current_phase_elapsed
            self.actual_phase_durations.append({
                'phase': self.current_phase.value,
                'duration': actual_duration
            })

            # Transition to next phase
            self.current_phase = self._get_next_phase()
            self.current_phase_elapsed = 0.0

        return self.current_phase
    
    def _get_next_phase(self) -> LightPhase:
        """Determine next phase in the cycle"""
        phase_sequence = [
            LightPhase.NORTH_SOUTH_GREEN,
            LightPhase.NORTH_SOUTH_YELLOW,
            LightPhase.ALL_RED,
            LightPhase.EAST_WEST_GREEN,
            LightPhase.EAST_WEST_YELLOW,
            LightPhase.ALL_RED
        ]
        
        current_index = phase_sequence.index(self.current_phase)
        next_index = (current_index + 1) % len(phase_sequence)
        return phase_sequence[next_index]
    
    def get_status(self) -> Dict:
        """
        Get complete status of traffic light controller with performance metrics.
        """
        return {
            'current_phase': self.current_phase.value,
            'time_in_phase': self.get_time_in_phase(),
            'remaining_time': self.get_remaining_time(),
            'vehicle_counts': self.vehicle_counts.copy(),
            'phase_timings': {k.value: v for k, v in self.phase_timings.items()},
            'performance': {
                'average_green_time': self._calculate_average_green_time(),
                'vehicle_throughput': self._calculate_vehicle_throughput(),
                'efficiency': self._calculate_efficiency()
            }
        }

    def _recalculate_timings(self):
        """Recalculate all phase timings based on current vehicle counts"""
        self.phase_timings[LightPhase.NORTH_SOUTH_GREEN] = \
            self._calculate_green_time('north', 'south')
        self.phase_timings[LightPhase.EAST_WEST_GREEN] = \
            self._calculate_green_time('east', 'west')

    def should_extend_current_phase(self) -> bool:
        """
        Check if current green phase should be extended based on vehicle presence.
        Uses gap time logic for more realistic behavior.
        """
        if self.current_phase not in (LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN):
            return False

        # Check if there are vehicles still waiting in the green direction
        if self.current_phase == LightPhase.NORTH_SOUTH_GREEN:
            total_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']
        else:
            total_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']

        # Extend if there are more vehicles than threshold
        return total_vehicles > self.config.vehicle_threshold

    def get_extension_time(self) -> float:
        """
        Calculate how much time to add to current green phase.
        Returns 0 if no extension needed.
        """
        if not self.should_extend_current_phase():
            return 0.0

        # Calculate based on vehicle gap time
        if self.current_phase == LightPhase.NORTH_SOUTH_GREEN:
            total_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']
        elif self.current_phase == LightPhase.EAST_WEST_GREEN:
            total_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']
        else:
            return 0.0

        # Calculate extension: (vehicles - threshold) * extension_per_vehicle
        # But don't exceed max_extension
        excess_vehicles = max(0, total_vehicles - self.config.vehicle_threshold)
        extension = min(excess_vehicles * self.config.extension_per_vehicle,
                       self.config.max_extension)

        return extension

    def get_time_in_phase(self) -> float:
        """Get elapsed time in current phase"""
        return self.current_phase_elapsed

    def get_remaining_time(self) -> float:
        """Get remaining time in current phase"""
        current_duration = self.phase_timings[self.current_phase]
        return max(0, current_duration - self.current_phase_elapsed)

    def _calculate_average_green_time(self) -> float:
        """
        Calculate average green time across all phases.
        """
        green_phases = [LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN]
        durations = [d['duration'] for d in self.actual_phase_durations 
                    if d['phase'] in [p.value for p in green_phases]]
        return sum(durations) / len(durations) if durations else 0.0

    def _calculate_vehicle_throughput(self) -> float:
        """
        Calculate vehicles processed per minute.
        """
        total_vehicles = sum(self.vehicle_counts.values())
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        return (total_vehicles / total_time) * 60 if total_time > 0 else 0.0

    def _calculate_efficiency(self) -> float:
        """
        Calculate efficiency as ratio of green time to total cycle time.
        """
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        green_time = sum(d['duration'] for d in self.actual_phase_durations 
                        if 'GREEN' in d['phase'])
        return (green_time / total_time) * 100 if total_time > 0 else 0.0