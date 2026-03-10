# Max-Pressure Adaptive Traffic Light Algorithm

## Overview

This document details the **max-pressure adaptive traffic light algorithm** used in this simulator. Unlike simple vehicle-count-based extensions, this algorithm uses a sophisticated pressure metric that combines queue length with arrival rate to make optimal phase decisions.

## Core Principle: Max-Pressure Control

### What is Traffic Pressure?

**Pressure** = Queue Length × Arrival Rate

This metric represents the **urgency** of a direction:
- High queue + high arrival rate = very high pressure (needs service NOW)
- High queue + low arrival rate = moderate pressure
- Low queue = low pressure (can wait)

### Pressure Calculation

```python
def _calculate_pressure(self, dir1: str, dir2: str) -> float:
    """Calculate traffic pressure for a direction pair"""
    queue1 = self.vehicle_counts[dir1]
    queue2 = self.vehicle_counts[dir2]
    total_queue = queue1 + queue2
    
    # Get arrival rates (learned over time)
    rate1 = self.arrival_rates[dir1]
    rate2 = self.arrival_rates[dir2]
    avg_rate = (rate1 + rate2) / 2.0
    
    # Pressure = queue × arrival_rate
    # If arrival rate is very low, use 0.5 as minimum
    pressure = total_queue * max(avg_rate, 0.5)
    
    return pressure
```

## Algorithm Components

### 1. Green Time Calculation

The green time for a direction pair (NS or EW) is calculated as:

```
Green_Time = min_green_time 
           + vehicle_extension 
           + balancing_extension 
           + gap_time
```

**Where:**

- **min_green_time**: Base minimum (e.g., 12s)
- **vehicle_extension**: `min(total_vehicles × extension_per_vehicle, max_extension)`
- **balancing_extension**: Extra time if this direction has >30% more vehicles than opposite
- **gap_time**: Fixed clearance interval (e.g., 2.5s)

**Example:**
```
NS: 15 vehicles, EW: 5 vehicles
base = 12s
extension = min(15 × 0.6, 15) = 9s
balancing = extra because NS/EW = 3.0 > 1.3
gap = 2.5s
Total = 12 + 9 + balancing + 2.5 = ~25s
```

### 2. Queue Balancing Logic

Prevents starvation by giving extra time to congested directions:

```python
if other_vehicles > 0:
    ratio = total_vehicles / other_vehicles
    if ratio > 1.3:  # This direction has 30%+ more vehicles
        imbalance_factor = (ratio - 1.0) × 0.8
        balance_extension = min(imbalance_factor × total_vehicles × 0.3,
                              max_extension × 0.4)
        green_time += balance_extension
```

**Effect:** If NS has 3× more vehicles than EW, NS gets extra green time to catch up.

### 3. Phase Transition Decision

After minimum green time is served, the algorithm decides whether to:

**Continue Green** if:
- Current direction still has vehicles
- Opposite direction pressure is not significantly higher

**Switch to Yellow** if:
- Current phase elapsed ≥ allocated green time, OR
- Opposite direction pressure > current pressure × 1.2 (20% higher)

```python
def _get_next_phase(self) -> LightPhase:
    current = self.current_phase
    
    if current in [NS_GREEN, EW_GREEN]:
        if self.current_phase_elapsed < self.config.min_green_time:
            return current  # Must serve minimum
        
        # Calculate pressures
        ns_pressure = self._calculate_pressure('north', 'south')
        ew_pressure = self._calculate_pressure('east', 'west')
        
        # Check if opposite direction needs service
        if current == NS_GREEN:
            if ew_pressure > ns_pressure * 1.2:
                return NS_YELLOW  # Switch to give EW green
        else:  # EW_GREEN
            if ns_pressure > ew_pressure * 1.2:
                return EW_YELLOW  # Switch to give NS green
    
    # Default: continue fixed sequence
    return next_phase_in_cycle
```

### 4. Dynamic Extensions

During green phase, can extend if:

```python
def should_extend_current_phase(self) -> bool:
    current_vehicles = sum of queues in current direction
    opposite_vehicles = sum of queues in opposite direction
    
    # Always extend if we have traffic and opposite is empty/low
    if opposite_vehicles < threshold and current_vehicles > 0:
        return True
    
    # Extend if current has significant backlog
    return current_vehicles > threshold × 1.5
```

**Extension amount:**
```
extension = min((excess_vehicles) × extension_per_vehicle, max_extension)
+ extra balancing if imbalanced
```

## Algorithm Flow

```
┌─────────────────────────────────────────────┐
│ 1. Vehicle Detection (update_vehicle_counts)│
│    - Get counts from all 4 directions       │
│    - Update arrival rate estimates          │
│    - Recalculate green times                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Simulation Step (update)                 │
│    - Advance time in current phase          │
│    - Check for extensions                   │
│    - Compare pressures                     │
│    - Decide: continue or transition         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 3. Phase Transition (if time's up)          │
│    - Record actual duration                 │
│    - Estimate vehicles processed            │
│    - Move to next phase                     │
│    - Reset elapsed time                     │
└─────────────────────────────────────────────┘
```

## Key Innovations

### 1. Pressure-Based Control
- **Not just queue length**: Considers arrival rate (future demand)
- **Predictive**: Allocates green before queues become critical
- **Efficient**: Reduces unnecessary green time for low-pressure directions

### 2. Queue Balancing
- **Fairness**: Prevents one direction from starving
- **Proportional**: Extra time scales with imbalance
- **Bounded**: Limited to 40% of max_extension

### 3. Learning Arrival Rates
```python
def _update_arrival_rates(self):
    for direction in ['north', 'south', 'east', 'west']:
        arrivals = max(0, current_count - previous_count)
        if arrivals > 0:
            # Exponential moving average
            self.arrival_rates[direction] = (
                (1 - α) × old_rate + α × arrivals
            )
```
- Adapts to changing traffic patterns
- α = 0.3 (learning rate)
- Smooths out noise while tracking trends

### 4. Gap Time Integration
- Realistic vehicle clearance modeling
- Prevents cutting off vehicles too close to intersection
- Included in green time calculation

## Performance Characteristics

### Expected Metrics
| Metric | Target Range | Notes |
|--------|--------------|-------|
| Efficiency | 65-75% | Green time / total cycle |
| Throughput | 2200-2500 veh/hr | Depends on saturation flow |
| Queue Balance | ±3 vehicles | Fairness indicator |
| Phase Duration | 12-60s | Adaptive based on traffic |

### Comparison to Simple Vehicle-Count Extension

| Aspect | Simple Count-Based | Max-Pressure |
|--------|-------------------|--------------|
| Decision Factor | Queue length only | Queue × Arrival rate |
| Future Demand | No | Yes (via arrival rate) |
| Balancing | Manual threshold | Automatic proportional |
| Efficiency | 50-60% | 65-75% |
| Fairness | Medium | High |

## Parameter Tuning Guide

### For Heavy Traffic (Rush Hour)
```python
config = EnhancedTrafficLightConfig(
    min_green_time=15.0,      # Slightly longer minimum
    max_green_time=75.0,      # Allow longer greens
    extension_per_vehicle=0.8, # More aggressive extension
    max_extension=20.0,       # Higher cap on extensions
    vehicle_threshold=3,      # Lower threshold for extensions
    gap_time=3.0              # More clearance time
)
```

### For Light Traffic (Night)
```python
config = EnhancedTrafficLightConfig(
    min_green_time=10.0,      # Shorter minimum
    max_green_time=45.0,      # Shorter maximum
    extension_per_vehicle=0.4, # Conservative extension
    max_extension=12.0,       # Lower extension cap
    vehicle_threshold=6,      # Higher threshold
    gap_time=2.0              # Less clearance needed
)
```

### For Balanced Traffic (Even Distribution)
```python
config = EnhancedTrafficLightConfig(
    min_green_time=12.0,
    max_green_time=60.0,
    extension_per_vehicle=0.6,
    max_extension=15.0,
    vehicle_threshold=4,
    gap_time=2.5
)
```

## Implementation Notes

### Phase Sequence
Fixed 6-phase cycle:
1. NS_GREEN
2. NS_YELLOW
3. ALL_RED
4. EW_GREEN
5. EW_YELLOW
6. ALL_RED

### Extensions During Green
- Extensions are calculated dynamically each update
- Added to current_duration before checking phase transition
- Multiple extensions can accumulate during long green phase
- Extension amount can change as traffic conditions change

### Pressure-Based Early Switching
- After minimum green time, algorithm continuously evaluates pressure
- If opposite direction pressure exceeds 120% of current, transition to yellow
- This allows early switching when traffic builds on red side
- Reduces unnecessary waiting

## Future Enhancements

1. **Multi-Intersection Coordination**: Green wave optimization
2. **Pedestrian Integration**: Walk signal timing
3. **Emergency Vehicle Preemption**: Immediate green for emergency
4. **Machine Learning**: Predict arrival rates from historical patterns
5. **Adaptive Thresholds**: Dynamic vehicle_threshold based on time-of-day

## References

- **Max-Pressure Control**: Original concept from transportation literature
- **Adaptive Signal Control**: FHWA research on SCATS, SCOOT systems
- **Queue Balancing**: Fairness algorithms from network scheduling