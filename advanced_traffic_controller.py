"""
Advanced Traffic Light Controller with Individual Direction Control
Adjusts signal timing for each direction (N, S, E, W) separately based on vehicle counts
"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple
import numpy as np


class LightPhase(Enum):
    """Traffic light phases for a 4-way intersection with individual direction control"""
    NORTH_GREEN = "N_GREEN"
    NORTH_YELLOW = "N_YELLOW"
    SOUTH_GREEN = "S_GREEN"
    SOUTH_YELLOW = "S_YELLOW"
    EAST_GREEN = "E_GREEN"
    EAST_YELLOW = "E_YELLOW"
    WEST_GREEN = "W_GREEN"
    WEST_YELLOW = "W_YELLOW"
    ALL_RED = "ALL_RED"


@dataclass
class AdvancedTrafficConfig:
    """Configuration for advanced traffic light timing with individual direction control"""
    min_green_time: float = 10.0  # Minimum green time in seconds
    max_green_time: float = 45.0  # Maximum green time in seconds
    yellow_time: float = 3.0  # Yellow light duration
    all_red_time: float = 2.0  # All-red clearance interval
    vehicle_threshold: int = 3   # Minimum vehicles to consider extension
    extension_per_vehicle: float = 0.8  # Seconds added per vehicle
    max_extension: float = 25.0  # Maximum extension beyond base time
    gap_time: float = 2.0  # Gap between last vehicle and phase end (seconds)
    min_phase_cycle: int = 2  # Minimum number of phases before returning to same direction
    pressure_threshold: float = 1.2  # Pressure ratio threshold for switching


class AdvancedTrafficController:
    """
    Advanced traffic light controller that treats each direction separately.
    Uses max-pressure algorithm to decide which direction gets green next.
    """
    
    def __init__(self, config: AdvancedTrafficConfig = None):
        self.config = config or AdvancedTrafficConfig()
        
        # Define all possible green phases (one for each direction)
        self.green_phases = [
            LightPhase.NORTH_GREEN,
            LightPhase.SOUTH_GREEN,
            LightPhase.EAST_GREEN,
            LightPhase.WEST_GREEN
        ]
        
        # Define yellow phases for each direction
        self.yellow_phases = {
            LightPhase.NORTH_GREEN: LightPhase.NORTH_YELLOW,
            LightPhase.SOUTH_GREEN: LightPhase.SOUTH_YELLOW,
            LightPhase.EAST_GREEN: LightPhase.EAST_YELLOW,
            LightPhase.WEST_GREEN: LightPhase.WEST_YELLOW
        }
        
        # Current state
        self.current_phase = LightPhase.ALL_RED
        self.current_phase_elapsed = 0.0
        self.last_green_direction = None
        self.phase_history = []  # Track recent phases to avoid starvation
        
        # Vehicle counts for each direction
        self.vehicle_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        
        # Arrival rate estimates (vehicles/sec) - learned over time
        self.arrival_rates = {
            'north': 0.5,
            'south': 0.5,
            'east': 0.5,
            'west': 0.5
        }
        
        # Previous counts for arrival rate calculation
        self._previous_counts = self.vehicle_counts.copy()
        
        # Phase timings (calculated dynamically)
        self.phase_timings = {}
        self._recalculate_all_timings()
        
        # Performance tracking
        self.actual_phase_durations = []
        self.total_vehicles_processed = 0
        self.direction_vehicles_processed = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        self.direction_changes = 0  # Count of phase transitions (green→yellow→all-red→next green)
        
    def update_vehicle_counts(self, north: int, south: int, east: int, west: int):
        """Update vehicle counts from detection system"""
        # Store previous counts for arrival rate calculation
        self._previous_counts = self.vehicle_counts.copy()
        
        # Update current counts
        self.vehicle_counts['north'] = north
        self.vehicle_counts['south'] = south
        self.vehicle_counts['east'] = east
        self.vehicle_counts['west'] = west
        
        # Update arrival rate estimates
        self._update_arrival_rates()
        
        # Recalculate phase timings based on new counts
        self._recalculate_all_timings()
    
    def _update_arrival_rates(self):
        """Update arrival rate estimates using exponential moving average"""
        for direction in ['north', 'south', 'east', 'west']:
            arrivals = max(0, self.vehicle_counts[direction] - self._previous_counts[direction])
            if arrivals > 0:
                # Exponential moving average with learning rate 0.3
                alpha = 0.3
                self.arrival_rates[direction] = (1 - alpha) * self.arrival_rates[direction] + alpha * arrivals
    
    def _recalculate_all_timings(self):
        """Recalculate green times for all directions based on current vehicle counts"""
        for direction, phase in [('north', LightPhase.NORTH_GREEN),
                                ('south', LightPhase.SOUTH_GREEN),
                                ('east', LightPhase.EAST_GREEN),
                                ('west', LightPhase.WEST_GREEN)]:
            self.phase_timings[phase] = self._calculate_green_time(direction)
        
        # Set fixed times for yellow and all-red phases
        self.phase_timings[LightPhase.ALL_RED] = self.config.all_red_time
        for yellow_phase in [LightPhase.NORTH_YELLOW, LightPhase.SOUTH_YELLOW,
                           LightPhase.EAST_YELLOW, LightPhase.WEST_YELLOW]:
            self.phase_timings[yellow_phase] = self.config.yellow_time
    
    def _calculate_green_time(self, direction: str) -> float:
        """Calculate adaptive green time for a specific direction"""
        vehicles = self.vehicle_counts[direction]
        
        if vehicles <= 0:
            return self.config.min_green_time
        
        # Base green time
        green_time = self.config.min_green_time
        
        # Extension based on vehicle count
        vehicle_extension = min(vehicles * self.config.extension_per_vehicle,
                              self.config.max_extension)
        green_time += vehicle_extension
        
        # Consider pressure from other directions
        # If this direction has significantly higher pressure than others, give more time
        pressure_ratio = self._get_pressure_ratio(direction)
        if pressure_ratio > 1.5:  # 50% higher pressure than average
            pressure_extension = min((pressure_ratio - 1.0) * 5.0,
                                   self.config.max_extension * 0.3)
            green_time += pressure_extension
        
        # Add gap time for vehicle clearance
        green_time += self.config.gap_time
        
        # Clamp to min/max bounds
        return max(self.config.min_green_time,
                  min(green_time, self.config.max_green_time))
    
    def _get_pressure_ratio(self, direction: str) -> float:
        """Calculate pressure ratio of this direction compared to average of others"""
        this_pressure = self._calculate_pressure(direction)
        
        # Calculate average pressure of other directions
        other_directions = [d for d in ['north', 'south', 'east', 'west'] if d != direction]
        other_pressures = [self._calculate_pressure(d) for d in other_directions]
        avg_other_pressure = sum(other_pressures) / len(other_pressures) if other_pressures else 0.5
        
        if avg_other_pressure == 0:
            return float('inf') if this_pressure > 0 else 1.0
        
        return this_pressure / avg_other_pressure
    
    def _calculate_pressure(self, direction: str) -> float:
        """Calculate traffic pressure for a specific direction"""
        queue = self.vehicle_counts[direction]
        arrival_rate = self.arrival_rates[direction]
        
        # Pressure = queue × arrival_rate (with minimum arrival rate)
        # Use sqrt to make it less aggressive (diminishing returns)
        pressure = (queue ** 0.7) * max(arrival_rate, 0.3)
        
        # Add penalty if this direction was recently served
        if self.last_green_direction == direction:
            # Recently served, reduce pressure significantly
            pressure *= 0.5
        
        # Add penalty based on how recently this direction was in phase history
        for i, hist_direction in enumerate(reversed(self.phase_history)):
            if hist_direction == direction:
                # The more recent, the higher the penalty
                recency_penalty = 1.0 / (i + 2)  # 0.5, 0.33, 0.25, ...
                pressure *= (1.0 - 0.4 * recency_penalty)  # Reduce by up to 40%
                break
        
        return pressure
    
    def update(self, delta_time: float = 1.0) -> LightPhase:
        """
        Update traffic light state based on elapsed time.
        Returns the new phase if changed, otherwise current phase.
        """
        # Advance time in current phase
        self.current_phase_elapsed += delta_time
        
        # Get current phase duration
        current_duration = self.phase_timings.get(self.current_phase, 0)
        
        # Check if we should extend current green phase
        extension = 0.0
        if self.current_phase in self.green_phases:
            extension = self._get_extension_time()
            if extension > 0:
                current_duration += extension
        
        # Force transition if we've exceeded maximum green time (including extensions)
        if self.current_phase in self.green_phases:
            base_green_time = self.phase_timings.get(self.current_phase, 0)
            max_total_time = base_green_time + self.config.max_extension
            if self.current_phase_elapsed >= max_total_time:
                # Clamp current_duration to max_total_time so normal transition logic will trigger
                # This ensures proper recording of phase duration and vehicle processing
                current_duration = max_total_time
        
        # Check if phase should transition
        if self.current_phase_elapsed >= current_duration:
            # Record actual duration
            self.actual_phase_durations.append({
                'phase': self.current_phase.value,
                'duration': self.current_phase_elapsed
            })
            
            # If this was a green phase, record vehicles processed
            if self.current_phase in self.green_phases:
                self._record_vehicles_processed()
                # Update last green direction
                self.last_green_direction = self._get_direction_from_phase(self.current_phase)
                # Add to phase history
                self.phase_history.append(self.last_green_direction)
                if len(self.phase_history) > 10:  # Keep last 10 phases
                    self.phase_history.pop(0)
            
            # Transition to next phase
            self.current_phase = self._get_next_phase()
            self.current_phase_elapsed = 0.0
            # Count direction change when we enter a new GREEN phase
            if self.current_phase in self.green_phases:
                self.direction_changes += 1
        
        return self.current_phase
    
    def _get_direction_from_phase(self, phase: LightPhase) -> str:
        """Get direction string from phase enum"""
        if phase == LightPhase.NORTH_GREEN or phase == LightPhase.NORTH_YELLOW:
            return 'north'
        elif phase == LightPhase.SOUTH_GREEN or phase == LightPhase.SOUTH_YELLOW:
            return 'south'
        elif phase == LightPhase.EAST_GREEN or phase == LightPhase.EAST_YELLOW:
            return 'east'
        elif phase == LightPhase.WEST_GREEN or phase == LightPhase.WEST_YELLOW:
            return 'west'
        return None
    
    def _get_next_phase(self) -> LightPhase:
        """Determine next phase using max-pressure algorithm"""
        current = self.current_phase
        
        # If we're in a green phase, transition to yellow
        if current in self.green_phases:
            return self.yellow_phases[current]
        
        # If we're in a yellow phase, transition to all-red
        elif current in [LightPhase.NORTH_YELLOW, LightPhase.SOUTH_YELLOW,
                        LightPhase.EAST_YELLOW, LightPhase.WEST_YELLOW]:
            return LightPhase.ALL_RED
        
        # If we're in ALL_RED, decide which direction gets green next
        elif current == LightPhase.ALL_RED:
            return self._select_next_green_phase()
        
        # Default fallback
        return LightPhase.ALL_RED
    
    def _select_next_green_phase(self) -> LightPhase:
        """Select which direction should get green next using max-pressure algorithm"""
        # Calculate pressure for all directions
        pressures = {}
        for direction in ['north', 'south', 'east', 'west']:
            pressures[direction] = self._calculate_pressure(direction)
        
        # Apply fairness: reduce pressure for recently served directions
        for i, direction in enumerate(reversed(self.phase_history)):
            age_factor = 1.0 / (i + 2)  # Older phases get less penalty
            pressures[direction] *= (1.0 - 0.3 * age_factor)  # Reduce by up to 30%
        
        # Enforce min_phase_cycle: prevent same direction from being selected too soon
        if len(self.phase_history) >= self.config.min_phase_cycle:
            most_recent = self.phase_history[-1]  # Last served direction
            # Check if we're about to select the same direction
            # If so, temporarily reduce its pressure significantly to force a different choice
            if most_recent in pressures:
                pressures[most_recent] *= 0.1  # 90% reduction to prevent immediate repeat
        
        # Find direction with maximum pressure
        max_direction = max(pressures.keys(), key=lambda d: pressures[d])
        
        # Convert direction to phase
        if max_direction == 'north':
            return LightPhase.NORTH_GREEN
        elif max_direction == 'south':
            return LightPhase.SOUTH_GREEN
        elif max_direction == 'east':
            return LightPhase.EAST_GREEN
        else:  # west
            return LightPhase.WEST_GREEN
    
    def _get_extension_time(self) -> float:
        """Calculate extension time for current green phase"""
        if self.current_phase not in self.green_phases:
            return 0.0
        
        direction = self._get_direction_from_phase(self.current_phase)
        if not direction:
            return 0.0
        
        vehicles = self.vehicle_counts[direction]
        
        # Check if extension is needed
        if vehicles < self.config.vehicle_threshold:
            return 0.0
        
        # Calculate extension based on excess vehicles
        excess_vehicles = vehicles - self.config.vehicle_threshold
        extension = min(excess_vehicles * self.config.extension_per_vehicle,
                       self.config.max_extension)
        
        # Check if other directions have low pressure
        other_directions = [d for d in ['north', 'south', 'east', 'west'] if d != direction]
        other_pressures = [self._calculate_pressure(d) for d in other_directions]
        max_other_pressure = max(other_pressures) if other_pressures else 0
        
        this_pressure = self._calculate_pressure(direction)
        
        # If this direction has much higher pressure, extend more
        if max_other_pressure > 0 and this_pressure / max_other_pressure > 2.0:
            extension *= 1.5  # Extend 50% more
        
        return min(extension, self.config.max_extension)
    
    def _record_vehicles_processed(self):
        """Estimate vehicles processed during current green phase (called automatically on phase transition)"""
        if self.current_phase not in self.green_phases:
            return

        direction = self._get_direction_from_phase(self.current_phase)
        if not direction:
            return

        # Estimate based on green duration and saturation flow (2 vehicles/sec)
        saturation_flow = 2.0  # vehicles per second
        estimated_processed = min(
            self.vehicle_counts[direction],
            saturation_flow * self.current_phase_elapsed
        )

        self.direction_vehicles_processed[direction] += estimated_processed
        self.total_vehicles_processed += estimated_processed

    def add_vehicles_processed(self, direction: str, count: int):
        """Add actual processed vehicles (called by simulator when known)"""
        if direction in ['north', 'south', 'east', 'west']:
            self.direction_vehicles_processed[direction] += count
            self.total_vehicles_processed += count
    
    def get_status(self) -> Dict:
        """Get complete status of traffic light controller"""
        # Calculate performance metrics
        efficiency = self._calculate_efficiency()
        throughput = self._calculate_throughput()
        
        return {
            'current_phase': self.current_phase.value,
            'time_in_phase': self.current_phase_elapsed,
            'remaining_time': self.get_remaining_time(),
            'vehicle_counts': self.vehicle_counts.copy(),
            'arrival_rates': self.arrival_rates.copy(),
            'phase_timings': {k.value: v for k, v in self.phase_timings.items()},
            'performance': {
                'efficiency': efficiency,
                'throughput': throughput,
                'vehicles_processed': self.total_vehicles_processed,
                'direction_processed': self.direction_vehicles_processed.copy(),
                'direction_changes': self.direction_changes
            },
            'pressures': {
                'north': self._calculate_pressure('north'),
                'south': self._calculate_pressure('south'),
                'east': self._calculate_pressure('east'),
                'west': self._calculate_pressure('west')
            }
        }
    
    def get_remaining_time(self) -> float:
        """Get remaining time in current phase"""
        current_duration = self.phase_timings.get(self.current_phase, 0)
        
        # Add extension if in green phase
        if self.current_phase in self.green_phases:
            extension = self._get_extension_time()
            current_duration += extension
        
        return max(0, current_duration - self.current_phase_elapsed)
    
    def _calculate_efficiency(self) -> float:
        """Calculate efficiency as ratio of green time to total cycle time"""
        if not self.actual_phase_durations:
            return 0.0
        
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        green_time = sum(d['duration'] for d in self.actual_phase_durations 
                        if any(green.value in d['phase'] for green in self.green_phases))
        
        return (green_time / total_time) * 100 if total_time > 0 else 0.0
    
    def _calculate_throughput(self) -> float:
        """Calculate vehicles processed per minute"""
        if not self.actual_phase_durations:
            return 0.0
        
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        return (self.total_vehicles_processed / total_time) * 60 if total_time > 0 else 0.0
    
    def get_red_time(self, direction: str) -> float:
        """Get estimated red time for a specific direction"""
        if direction not in ['north', 'south', 'east', 'west']:
            return 0.0
        
        # If currently green for this direction, red time is 0
        current_direction = self._get_direction_from_phase(self.current_phase)
        if current_direction == direction and self.current_phase in self.green_phases:
            return 0.0
        
        # Estimate time until this direction gets green
        # This is a simplified estimation
        remaining = self.get_remaining_time()
        
        # If we're in yellow or all-red for this direction, add those times
        if (direction == 'north' and self.current_phase in [LightPhase.NORTH_YELLOW, LightPhase.ALL_RED]) or \
           (direction == 'south' and self.current_phase in [LightPhase.SOUTH_YELLOW, LightPhase.ALL_RED]) or \
           (direction == 'east' and self.current_phase in [LightPhase.EAST_YELLOW, LightPhase.ALL_RED]) or \
           (direction == 'west' and self.current_phase in [LightPhase.WEST_YELLOW, LightPhase.ALL_RED]):
            return remaining
        
        # Otherwise, this direction is red and will need to wait
        # Estimate based on average phase times
        avg_green_time = self.config.min_green_time + (self.config.max_green_time - self.config.min_green_time) / 2
        avg_cycle_time = avg_green_time * 4 + self.config.yellow_time * 4 + self.config.all_red_time
        
        # Simplified: assume we're somewhere in the cycle
        return avg_cycle_time / 4  # Rough estimate