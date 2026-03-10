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
        # Define phase sequence with unique tracking
        self._phase_sequence = [
            LightPhase.NORTH_SOUTH_GREEN,
            LightPhase.NORTH_SOUTH_YELLOW,
            LightPhase.ALL_RED,
            LightPhase.EAST_WEST_GREEN,
            LightPhase.EAST_WEST_YELLOW,
            LightPhase.ALL_RED
        ]
        self._current_phase_index = 0
        self.current_phase = self._phase_sequence[self._current_phase_index]
        self.current_phase_elapsed = 0.0  # Simulation time in current phase
        self.vehicle_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        # Track previous counts for pressure calculation
        self._previous_counts = {
            'north': 0,
            'south': 0,
            'east': 0,
            'west': 0
        }
        # Arrival rate estimates (vehicles/sec) - can be learned over time
        self.arrival_rates = {
            'north': getattr(config, 'arrival_rate', 0.6),
            'south': getattr(config, 'arrival_rate', 0.6),
            'east': getattr(config, 'arrival_rate', 0.6),
            'west': getattr(config, 'arrival_rate', 0.6)
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
        self.total_vehicles_processed = 0
        
    def update_vehicle_counts(self, north: int, south: int, east: int, west: int):
        """Update vehicle counts from CNN detection (4 cameras)"""
        # Store previous counts for pressure calculation
        self._previous_counts = {
            'north': self.vehicle_counts['north'],
            'south': self.vehicle_counts['south'],
            'east': self.vehicle_counts['east'],
            'west': self.vehicle_counts['west']
        }
        self.vehicle_counts['north'] = north
        self.vehicle_counts['south'] = south
        self.vehicle_counts['east'] = east
        self.vehicle_counts['west'] = west

        # Update arrival rate estimates based on new arrivals
        self._update_arrival_rates()

        # Recalculate green times based on new counts
        self._recalculate_timings()

    def _update_arrival_rates(self):
        """Update arrival rate estimates based on observed changes"""
        for direction in ['north', 'south', 'east', 'west']:
            # Calculate arrivals since last update
            arrivals = max(0, self.vehicle_counts[direction] - self._previous_counts[direction])
            if arrivals > 0:
                # Exponential moving average for arrival rate
                alpha = 0.3  # Learning rate
                self.arrival_rates[direction] = (1 - alpha) * self.arrival_rates[direction] + alpha * arrivals

    def add_vehicles_processed(self, count: int):
        """Add to total vehicles processed count"""
        self.total_vehicles_processed += count
    
    def _calculate_green_time(self, dir1: str, dir2: str) -> float:
        """Calculate adaptive green time based on vehicle counts with balancing."""
        total_vehicles = self.vehicle_counts[dir1] + self.vehicle_counts[dir2]

        if total_vehicles <= 0:
            return self.config.min_green_time

        # Determine which direction pair we're calculating for
        is_ns = dir1 in ['north', 'south']
        other_dir1 = 'east' if is_ns else 'north'
        other_dir2 = 'west' if is_ns else 'south'
        other_vehicles = self.vehicle_counts[other_dir1] + self.vehicle_counts[other_dir2]

        # Base time
        green_time = self.config.min_green_time

        # Basic extension based on absolute vehicle count
        base_extension = min(total_vehicles * self.config.extension_per_vehicle,
                           self.config.max_extension)
        green_time += base_extension

        # BALANCING: Add extra time if this direction has significantly more vehicles
        # This helps equalize queue lengths over time
        if other_vehicles > 0:
            ratio = total_vehicles / other_vehicles
            if ratio > 1.3:  # This direction has >30% more vehicles
                # Give extra time proportional to the imbalance
                imbalance_factor = (ratio - 1.0) * 0.8
                balance_extension = min(imbalance_factor * total_vehicles * 0.3,
                                      self.config.max_extension * 0.4)
                green_time += balance_extension
        elif total_vehicles > 0 and other_vehicles == 0:
            # Other direction is empty, but we still need minimum service
            # Don't over-extend, but ensure we clear this direction
            green_time += min(total_vehicles * 0.2, self.config.max_extension * 0.3)

        # Add gap time for vehicle clearance
        green_time += self.config.gap_time

        # Clamp to min/max bounds
        return max(self.config.min_green_time,
                  min(green_time, self.config.max_green_time))
    
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

            # If this was a green phase, estimate vehicles processed
            if self.current_phase in (LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN):
                self._record_vehicles_processed(actual_duration)

            # Transition to next phase
            self.current_phase = self._get_next_phase()
            self.current_phase_elapsed = 0.0

        return self.current_phase
    
    def _get_next_phase(self) -> LightPhase:
        """Determine next phase using max-pressure control for optimal efficiency"""
        current = self.current_phase

        # If we're in a green phase, check if we should switch to opposite direction
        if current in (LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN):
            # Only consider switching after minimum green time
            if self.current_phase_elapsed < self.config.min_green_time:
                return current  # Stay in current phase

            # Calculate max-pressure for each direction pair
            ns_pressure = self._calculate_pressure('north', 'south')
            ew_pressure = self._calculate_pressure('east', 'west')

            # If opposite direction has significantly higher pressure, consider switching
            if current == LightPhase.NORTH_SOUTH_GREEN:
                if ew_pressure > ns_pressure * 1.2:  # 20% higher pressure
                    # Queue for yellow -> all-red -> opposite green
                    return LightPhase.NORTH_SOUTH_YELLOW
            else:  # EW_GREEN
                if ns_pressure > ew_pressure * 1.2:
                    return LightPhase.EAST_WEST_YELLOW

        # Default: continue with fixed sequence
        self._current_phase_index = (self._current_phase_index + 1) % len(self._phase_sequence)
        return self._phase_sequence[self._current_phase_index]

    def _calculate_pressure(self, dir1: str, dir2: str) -> float:
        """Calculate traffic pressure for a direction pair using queue length and arrival rate"""
        queue1 = self.vehicle_counts[dir1]
        queue2 = self.vehicle_counts[dir2]
        total_queue = queue1 + queue2

        # Get arrival rates for these directions
        rate1 = self.arrival_rates[dir1]
        rate2 = self.arrival_rates[dir2]
        avg_rate = (rate1 + rate2) / 2.0

        # Pressure = queue * arrival_rate (expected vehicles arriving during red)
        # If arrival rate is low, use queue as proxy
        pressure = total_queue * max(avg_rate, 0.5)

        return pressure
    
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
        Check if current green phase should be extended based on vehicle presence
        and queue balance considerations.
        """
        if self.current_phase not in (LightPhase.NORTH_SOUTH_GREEN, LightPhase.EAST_WEST_GREEN):
            return False

        # Determine current and opposite directions
        if self.current_phase == LightPhase.NORTH_SOUTH_GREEN:
            current_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']
            opposite_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']
        else:
            current_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']
            opposite_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']

        # Always extend if we have vehicles and opposite direction is empty or low
        if opposite_vehicles < self.config.vehicle_threshold and current_vehicles > 0:
            return True

        # Extend if current direction has significant backlog
        return current_vehicles > self.config.vehicle_threshold * 1.5

    def get_extension_time(self) -> float:
        """
        Calculate how much time to add to current green phase.
        Returns 0 if no extension needed.
        """
        if not self.should_extend_current_phase():
            return 0.0

        # Determine current and opposite directions
        if self.current_phase == LightPhase.NORTH_SOUTH_GREEN:
            current_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']
            opposite_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']
        elif self.current_phase == LightPhase.EAST_WEST_GREEN:
            current_vehicles = self.vehicle_counts['east'] + self.vehicle_counts['west']
            opposite_vehicles = self.vehicle_counts['north'] + self.vehicle_counts['south']
        else:
            return 0.0

        # Base extension based on excess vehicles
        excess_vehicles = max(0, current_vehicles - self.config.vehicle_threshold)
        base_extension = min(excess_vehicles * self.config.extension_per_vehicle,
                            self.config.max_extension)

        # BALANCED EXTENSION: If current direction has much more traffic, give extra time
        # to help catch up, but not at the expense of completely starving the other direction
        if opposite_vehicles > 0:
            ratio = current_vehicles / max(1, opposite_vehicles)
            if ratio > 1.5:  # Current direction has 50%+ more vehicles
                # Add extra extension proportional to the imbalance
                extra_extension = min((ratio - 1.0) * 5.0, self.config.max_extension * 0.3)
                base_extension += extra_extension

        # Clamp to max extension
        return min(base_extension, self.config.max_extension)

    def _record_vehicles_processed(self, green_duration: float):
        """Estimate number of vehicles processed during green phase"""
        if self.current_phase == LightPhase.NORTH_SOUTH_GREEN:
            directions = ['north', 'south']
        elif self.current_phase == LightPhase.EAST_WEST_GREEN:
            directions = ['east', 'west']
        else:
            return

        # Calculate vehicles that could have been processed based on saturation flow
        saturation_flow = getattr(self.config, 'saturation_flow', 2.0)  # vehicles/sec
        total_processed = 0
        for direction in directions:
            queue_before = self.vehicle_counts[direction]
            # Estimate processed: min(queue_before, saturation_flow * duration)
            processed = min(queue_before, saturation_flow * green_duration)
            total_processed += processed

        self.total_vehicles_processed += total_processed

    def get_time_in_phase(self) -> float:
        """Get elapsed time in current phase"""
        return self.current_phase_elapsed

    def get_remaining_time(self) -> float:
        """Get remaining time in current phase"""
        current_duration = self.phase_timings[self.current_phase]
        return max(0, current_duration - self.current_phase_elapsed)

    def get_red_time(self, direction: str) -> float:
        """Get estimated red time for a specific direction (N, S, E, or W)"""
        # Determine which phase gives green to this direction
        if direction in ['north', 'south']:
            green_phase = LightPhase.NORTH_SOUTH_GREEN
        else:
            green_phase = LightPhase.EAST_WEST_GREEN

        # If currently green for this direction, red time is 0
        if self.current_phase == green_phase:
            return 0.0

        # Calculate time until next green for this direction
        time_remaining = 0
        current_index = self._phase_sequence.index(self.current_phase)
        steps = 0
        max_steps = len(self._phase_sequence)

        # Walk through phase cycle until we find the green phase
        while steps < max_steps:
            idx = (current_index + steps) % max_steps
            phase = self._phase_sequence[idx]
            if phase == green_phase:
                break
            # Add duration of this phase
            if phase in self.phase_timings:
                time_remaining += self.phase_timings[phase]
            steps += 1

        # Subtract elapsed time in current phase
        time_remaining -= self.current_phase_elapsed
        return max(0, time_remaining)

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
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        # Use total vehicles processed, not current queue
        return (self.total_vehicles_processed / total_time) * 60 if total_time > 0 else 0.0

    def _calculate_efficiency(self) -> float:
        """
        Calculate efficiency as ratio of green time to total cycle time.
        """
        total_time = sum(d['duration'] for d in self.actual_phase_durations)
        green_time = sum(d['duration'] for d in self.actual_phase_durations 
                        if 'GREEN' in d['phase'])
        return (green_time / total_time) * 100 if total_time > 0 else 0.0