# Max-Pressure Adaptive Traffic Light Algorithm (Individual Direction)

## Overview

This document details the **advanced max-pressure adaptive traffic light algorithm** with **individual direction control**. Unlike the older paired-direction system (NS/EW), this algorithm treats each direction (North, South, East, West) separately, allowing for optimal, asymmetric traffic management.

## Core Principle: Individual Direction Max-Pressure

### What is Traffic Pressure?

**Pressure(direction)** = (Queue_Length^0.7) × max(Arrival_Rate, 0.3)

This metric represents the **urgency** of a specific direction:
- High queue + high arrival rate = very high pressure (needs service NOW)
- Queue^0.7 provides diminishing returns (prevents monopoly by extremely long queues)
- Minimum arrival rate of 0.3 ensures all directions have baseline pressure
- Low queue = low pressure (can wait)

### Why Individual Direction?

The old system paired North+South and East+West, which works well for balanced traffic but fails when:
- One direction in a pair is heavy, the other is light (wastes green time)
- Traffic is highly asymmetric (e.g., only North is heavy)
- Different directions have vastly different arrival patterns

**Individual control** solves these by serving the most urgent direction regardless of pairing.

## Algorithm Components

### 1. Pressure Calculation (Per Direction)

```python
def _calculate_pressure(self, direction: str) -> float:
    """Calculate traffic pressure for a specific direction"""
    queue = self.vehicle_counts[direction]
    arrival_rate = self.arrival_rates[direction]
    
    # Base pressure with diminishing returns on queue
    pressure = (queue ** 0.7) * max(arrival_rate, 0.3)
    
    # Fairness: reduce pressure if this direction was recently served
    if self.last_green_direction == direction:
        pressure *= 0.5  # 50% reduction
    
    # Additional recency penalty from phase history
    for i, hist_direction in enumerate(reversed(self.phase_history)):
        if hist_direction == direction:
            recency_penalty = 1.0 / (i + 2)  # 0.5, 0.33, 0.25, ...
            pressure *= (1.0 - 0.4 * recency_penalty)  # Up to 40% reduction
            break
    
    return pressure
```

**Example Calculation:**
```
North: queue=15, arrival_rate=1.2, was served 2 phases ago
Base: 15^0.7 × 1.2 = 6.1 × 1.2 = 7.3
Recency penalty (i=1): 1.0 - 0.4/3 = 0.87
Final: 7.3 × 0.87 = 6.4
```

### 2. Green Time Calculation (Per Direction)

```
Green_Time = min_green_time
           + vehicle_extension
           + pressure_extension (if pressure_ratio > 1.5)
           + gap_time
```

**Components:**

- **min_green_time**: Base minimum (e.g., 10s) - ensures minimum service
- **vehicle_extension**: `min(vehicles × extension_per_vehicle, max_extension)`
  - Scales with current queue size
  - Capped to prevent excessive duration
- **pressure_extension**: Extra time if this direction's pressure >150% of average of others
  - `min((pressure_ratio - 1.0) × 5.0, max_extension × 0.3)`
  - Rewards truly urgent directions
- **gap_time**: Safety clearance (e.g., 2s) - allows last vehicles to clear

**Example:**
```
North: 20 vehicles, pressure_ratio = 2.1
Base = 10s
Vehicle ext = min(20 × 0.8, 25) = 16s
Pressure ext = min((2.1-1.0)×5.0, 25×0.3) = min(5.5, 7.5) = 5.5s
Gap = 2s
Total = 10 + 16 + 5.5 + 2 = 33.5s (within max 45s)
```

### 3. Phase Selection Algorithm

The system uses **dynamic priority-based selection** rather than fixed sequence:

**During GREEN phase:**
- Must serve at least `min_green_time`
- Can extend dynamically based on traffic
- Force transition after `base_green + max_extension`
- Early transition if other directions become much more urgent

**During YELLOW → ALL_RED → decision:**
1. Calculate pressure for all 4 directions (with fairness penalties)
2. Apply additional recency penalties to phase history
3. Select direction with highest adjusted pressure
4. Return corresponding GREEN phase

**Recency Penalty in Selection:**
```python
for i, direction in enumerate(reversed(self.phase_history)):
    age_factor = 1.0 / (i + 2)  # 0.5, 0.33, 0.25, ...
    pressures[direction] *= (1.0 - 0.3 * age_factor)  # Up to 30% reduction
```

This ensures recently served directions are less likely to be selected immediately.

### 4. Extension Logic During Green

While in a green phase, the algorithm can dynamically extend the duration:

**Extension Conditions:**
- Current direction has vehicles ≥ threshold (default 3)
- Extensions calculated each update (can change over time)
- Multiple extensions can accumulate

**Extension Amount:**
```python
excess = vehicles - threshold
extension = min(excess × extension_per_vehicle, max_extension)

# Bonus extension if this direction's pressure >> others
if this_pressure / max_other_pressure > 2.0:
    extension *= 1.5  # 50% bonus
```

**Example:**
```
Current: North GREEN, 12 vehicles, threshold=3
excess = 9, extension = min(9×0.8, 25) = 7.2s
If North pressure is 3× higher than any other: 7.2 × 1.5 = 10.8s added
```

## Algorithm Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Vehicle Detection (update_vehicle_counts)               │
│    - Get counts from all 4 directions                      │
│    - Update arrival rate estimates (EMA, α=0.3)            │
│    - Recalculate green times for all 4 directions          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Simulation Step (update)                                │
│    - Advance time in current phase                         │
│    - Check for extensions (get_extension_time)             │
│    - Compare pressures (for early transition)             │
│    - Decide: continue or transition                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Phase Transition (if time's up)                         │
│    - Record actual duration                                │
│    - Estimate vehicles processed                           │
│    - Update last_green_direction and phase_history        │
│    - Move to next phase (via _get_next_phase)             │
│    - Reset elapsed time                                    │
└─────────────────────────────────────────────────────────────┘
```

## Phase Sequence (Dynamic)

Unlike the fixed 6-phase cycle of the paired system, the individual direction system has a **variable sequence**:

```
ALL_RED → (select highest adjusted pressure) → GREEN → YELLOW → ALL_RED → repeat
```

The order of directions served depends entirely on traffic conditions. The system maintains a minimum of `min_phase_cycle` (default 2) cycles before the same direction can be selected again, preventing rapid oscillation.

**Typical Patterns:**
- **Heavy North**: N → S → E → W → N (if North remains heavy)
- **Balanced**: Random order based on slight pressure differences
- **Asymmetric**: Serves heavy directions more frequently, but all get service

**Phase Cycle:**
```
NORTH_GREEN (adaptive time) → NORTH_YELLOW (3s) → ALL_RED (2s) →
SOUTH_GREEN (adaptive time) → SOUTH_YELLOW (3s) → ALL_RED (2s) →
EAST_GREEN (adaptive time) → EAST_YELLOW (3s) → ALL_RED (2s) →
WEST_GREEN (adaptive time) → WEST_YELLOW (3s) → ALL_RED (2s) →
(repeat with new selection)
```

Note: The sequence order can vary based on pressure calculations. The above shows one possible order.

## Key Innovations

### 1. Individual Direction Control
- **Separate treatment**: Each direction gets independent green time
- **Asymmetric handling**: Perfect for highly unbalanced traffic
- **No wasted green**: Never serves empty directions in a pair

### 2. Pressure with Diminishing Returns
- **Queue^0.7**: Prevents monopoly by extremely long queues
- **Example**: queue=100 → 100^0.7 = 25.1 (not 100)
- Ensures fairness while still prioritizing high demand

### 3. Multi-Layer Fairness
- **Recency penalty**: Just-served directions get 50% pressure reduction
- **Phase history**: Up to 30% penalty for directions in last 10 phases
- **Minimum cycle**: Configurable minimum cycles before returning
- **Pressure threshold**: Only extend if pressure ratio > 1.5

### 4. Learning Arrival Rates
```python
def _update_arrival_rates(self):
    for direction in ['north', 'south', 'east', 'west']:
        arrivals = max(0, current_count - previous_count)
        if arrivals > 0:
            # Exponential moving average with α=0.3
            self.arrival_rates[direction] = (
                (1 - 0.3) * old_rate + 0.3 * arrivals
            )
```
- Adapts to changing traffic patterns (rush hour, incidents)
- α = 0.3 provides smooth learning without overreacting
- Each direction learns independently

### 5. Dynamic Extensions with Pressure Bonus
- Base extension based on vehicle count
- Additional 50% bonus if this direction's pressure is >2× others
- Ensures truly urgent directions get extra time

## Performance Characteristics

### Expected Metrics
| Metric | Target Range | Notes |
|--------|--------------|-------|
| Efficiency | 70-80% | Green time / total cycle (higher than paired system) |
| Throughput | 2500-3000 veh/hr | Depends on saturation flow |
| Queue Balance | ±2 vehicles | Excellent fairness across all 4 directions |
| Phase Duration | 8-45s | Adaptive based on traffic (more variable than paired) |
| Response Time | <30s for new traffic | Fast recognition of new demand |

### Comparison to Paired System

| Aspect | Paired (NS/EW) | Individual (N/S/E/W) |
|--------|----------------|---------------------|
| Control granularity | Direction pairs | Individual directions |
| Fairness | Good (between pairs) | Excellent (all 4 directions) |
| Adaptability | Moderate | High |
| Efficiency | 65-75% | 70-80% |
| Response to asymmetry | Limited | Excellent |
| Phase count | 6 fixed | 9 dynamic |
| Complexity | Lower | Higher |
| Best use case | Balanced traffic | Asymmetric traffic |

## Parameter Tuning Guide

### For Heavy Traffic (Rush Hour)
```python
config = AdvancedTrafficConfig(
    min_green_time=12.0,      # Slightly longer minimum
    max_green_time=50.0,      # Allow longer greens
    extension_per_vehicle=0.9, # More aggressive extension
    max_extension=30.0,       # Higher cap on extensions
    vehicle_threshold=2,      # Lower threshold for extensions
    gap_time=2.5,             # Standard clearance
    pressure_threshold=1.3    # More sensitive to pressure differences
)
```

### For Light Traffic (Night)
```python
config = AdvancedTrafficConfig(
    min_green_time=8.0,       # Shorter minimum
    max_green_time=30.0,      # Shorter maximum
    extension_per_vehicle=0.4, # Conservative extension
    max_extension=15.0,       # Lower extension cap
    vehicle_threshold=5,      # Higher threshold
    gap_time=2.0,             # Less clearance needed
    pressure_threshold=1.5    # Less sensitive switching
)
```

### For Highly Asymmetric Traffic
```python
config = AdvancedTrafficConfig(
    min_green_time=10.0,
    max_green_time=45.0,
    extension_per_vehicle=1.0,  # Very aggressive extensions
    max_extension=30.0,
    vehicle_threshold=2,
    gap_time=2.5,
    pressure_threshold=1.2,     # Switch more readily
    min_phase_cycle=1           # Allow quicker return to heavy direction
)
```

### For Balanced Traffic
```python
config = AdvancedTrafficConfig(
    min_green_time=10.0,
    max_green_time=40.0,
    extension_per_vehicle=0.6,
    max_extension=20.0,
    vehicle_threshold=4,
    gap_time=2.0,
    pressure_threshold=1.4,     # Less sensitive, more stable
    min_phase_cycle=3           # Force more even distribution
)
```

## Implementation Notes

### Phase History Management
- Stores last 10 served directions (as strings: 'north', 'south', 'east', 'west')
- Used to apply recency penalties during phase selection
- Prevents any direction from being served twice in quick succession
- Older entries have diminishing penalty effect

### Extension Calculation Timing
- Extensions are recalculated **every update** while in green phase
- Extension amount can increase or decrease as traffic changes
- Multiple extensions can accumulate (each adds to current_duration)
- Maximum total time = base_green_time + max_extension

### Pressure-Based Early Switching
- After minimum green time, algorithm checks pressures each update
- If any other direction's pressure exceeds current's by >20% (configurable via pressure_threshold), transition to yellow
- This allows urgent directions to be served quickly
- Prevents wasting green time when traffic pattern shifts

### Vehicle Processing Estimation
When a green phase ends, the system estimates vehicles processed:
```python
estimated_processed = min(
    vehicle_count_at_start,
    saturation_flow (2.0 veh/s) × actual_green_duration
)
```
This is added to `total_vehicles_processed` and `direction_vehicles_processed[direction]`.

## Future Enhancements

1. **Multi-Intersection Coordination**: Green wave optimization across network
2. **Pedestrian Integration**: Dedicated walk phases with button requests
3. **Emergency Vehicle Preemption**: Immediate override for emergencies
4. **Machine Learning**: Predict arrival rates from historical patterns
5. **Adaptive Thresholds**: Dynamic vehicle_threshold based on time-of-day
6. **Turning Movements**: Separate phases for left/right turns
7. **Queue Length Prediction**: Forecast queue growth during red
8. **Environmental Optimization**: Minimize emissions and fuel consumption

## References

- **Max-Pressure Control**: Original concept from transportation literature (Wong, 1996)
- **Adaptive Signal Control**: FHWA research on SCATS, SCOOT systems
- **Queue Balancing**: Fairness algorithms from network scheduling
- **Diminishing Returns**: Economic principle applied to queue pressure

## Migration from Paired System

If you're currently using the paired-direction system:

1. **Replace imports**:
   ```python
   # Old
   from traffic_light_controller import TrafficLightController, EnhancedTrafficLightConfig
   
   # New
   from advanced_traffic_controller import AdvancedTrafficController, AdvancedTrafficConfig
   ```

2. **Update configuration**:
   ```python
   # Old
   config = EnhancedTrafficLightConfig(min_green_time=12.0, ...)
   
   # New
   config = AdvancedTrafficConfig(min_green_time=10.0, ...)
   ```

3. **No code changes needed** if using `AdvancedTrafficSimulator` - it's already configured for individual control.

4. **Expected improvements**: 5-10% higher efficiency, better fairness, superior handling of asymmetric traffic.

5. **Parameter differences**: Individual system uses different defaults (lower min_green, higher max_extension, different thresholds). Tune for your intersection.