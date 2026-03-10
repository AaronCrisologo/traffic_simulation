# Code Architecture and Workflow Documentation

## System Overview

The traffic simulator implements a **max-pressure adaptive control algorithm** with modular architecture for easy maintenance and extension. The system separates concerns into distinct components: control logic, simulation engine, visualization, and configuration.

## Core Components

### 1. AdvancedTrafficController (Individual Direction Control)
**Location**: `advanced_traffic_controller.py`

**Purpose**: Max-pressure adaptive traffic light control with individual direction treatment

**Key Features**:
- Individual direction pressure calculation (N, S, E, W separately)
- Pressure formula: `(queue^0.7) × max(arrival_rate, 0.3)`
- Fairness penalties: 50% reduction for just-served, up to 30% for recent history
- Dynamic green time per direction with pressure-based extensions
- Phase history tracking (last 10 phases) to prevent starvation
- Arrival rate learning (EMA with α=0.3)
- Performance metrics tracking

**Main Methods**:
```python
def update(self, delta_time: float) -> LightPhase
    # Advances simulation time, checks for phase transitions
    # Returns new phase if changed

def update_vehicle_counts(self, north, south, east, west)
    # Updates vehicle counts, recalculates timings, updates arrival rates

def get_status(self) -> Dict
    # Returns complete status: phase, timings, pressures, performance

def _calculate_pressure(self, direction: str) -> float
    # Calculates pressure for individual direction with fairness penalties

def _calculate_green_time(self, direction: str) -> float
    # Computes adaptive green time for specific direction

def _select_next_green_phase(self) -> LightPhase
    # Max-pressure selection: chooses direction with highest adjusted pressure

def _get_extension_time(self) -> float
    # Calculates extension for current green based on traffic conditions
```

**Phase Sequence**: 9-phase cycle (NORTH_GREEN → NORTH_YELLOW → ALL_RED → SOUTH_GREEN → SOUTH_YELLOW → ALL_RED → EAST_GREEN → EAST_YELLOW → ALL_RED → WEST_GREEN → WEST_YELLOW → ALL_RED), but selection is dynamic based on pressure.

### 2. AdvancedTrafficSimulator
**Location**: `advanced_simulation.py`

**Purpose**: Advanced simulation with individual direction control and rich visualization

**Key Features**:
- Poisson traffic generation with time-of-day patterns (rush hour multipliers)
- Individual direction discharge at saturation flow
- Real-time ASCII intersection display with 4-direction metrics
- Comprehensive history recording (queues, pressures, green times per direction)
- Performance metrics (efficiency, throughput, per-direction processing)
- Configurable via AdvancedTrafficConfig

**Main Methods**:
```python
def __init__(self, controller_config: AdvancedTrafficConfig)
    # Initializes controller and simulation state

def generate_traffic(self, delta_time)
    # Generates arrivals using Poisson process with rush-hour cycles

def discharge_traffic(self, green_direction, delta_time) -> int
    # Removes vehicles from specific green direction at saturation flow

def update(self, delta_time=1.0) -> Dict
    # Executes one simulation step, returns phase, queues, pressures

def run(self, steps=200, delay=0.2, display=True)
    # Main loop with ASCII display and metrics

def display_intersection(self, result: dict)
    # Rich ASCII visualization showing all 4 directions with lights

def print_step_summary(self, step, result)
    # One-line summary for each step
```

### 3. TrafficLightController (Paired Direction Control)
**Location**: `traffic_light_controller.py`

**Purpose**: Original max-pressure adaptive controller with NS/EW pairing

**Key Features**:
- Paired direction pressure (NS vs EW)
- Queue balancing between pairs
- Dynamic green time for pairs
- Arrival rate learning
- Performance metrics

**Note**: This is the older system. The advanced system above is recommended for new deployments.

### 4. SimpleTrafficSimulator
**Location**: `simple_simulation.py`

**Purpose**: Basic simulation with paired direction control

**Key Features**:
- Poisson traffic generation
- Paired direction discharge (NS or EW)
- ASCII visualization
- History tracking
- Uses EnhancedTrafficLightConfig

**Note**: This works with the older paired-direction controller.

### 3. TrafficVisualizer
**Location**: `visualize.py`

**Purpose**: Advanced graphical visualization with 6+ real-time charts

**Key Features**:
- 6 interactive subplots (3×2 grid)
- Real-time updates with sliding window (default 100 points)
- Final static analysis with summary statistics
- Tracks 12+ metrics including pressure, balance, cumulative throughput

**Main Methods**:
```python
def __init__(self, simulator, max_points=200)
    # Sets up 6 axes and data arrays

def update(self, step, result, status)
    # Updates all charts with new data point

def final_plot(self)
    # Creates comprehensive final analysis with statistics box

def _generate_summary_text(self) -> str
    # Computes and formats key statistics
```

### 4. Configuration Classes

#### AdvancedTrafficConfig (Individual Direction)
**Location**: `advanced_traffic_controller.py`

**Purpose**: Configuration for advanced individual direction control

**Key Parameters**:
```python
@dataclass
class AdvancedTrafficConfig:
    min_green_time: float = 10.0      # Minimum green per direction
    max_green_time: float = 45.0      # Maximum green per direction
    yellow_time: float = 3.0          # Yellow duration
    all_red_time: float = 2.0         # All-red clearance
    vehicle_threshold: int = 3        # Min vehicles for extension
    extension_per_vehicle: float = 0.8  # Seconds per vehicle
    max_extension: float = 25.0       # Max extension cap
    gap_time: float = 2.0             # Clearance gap
    min_phase_cycle: int = 2          # Min cycles before returning
    pressure_threshold: float = 1.2   # Pressure ratio for switching
```

#### EnhancedTrafficLightConfig (Paired Directions)
**Location**: `enhanced_config.py`

**Purpose**: Configuration for original paired direction control

**Key Parameters**:
```python
@dataclass
class EnhancedTrafficLightConfig:
    min_green_time: float = 12.0
    max_green_time: float = 60.0
    yellow_time: float = 3.5
    all_red_time: float = 2.0
    vehicle_threshold: int = 4
    extension_per_vehicle: float = 0.6
    max_extension: float = 15.0
    gap_time: float = 2.5
    arrival_rate: float = 1.0
    saturation_flow: float = 2.5
```

## Data Flow Architecture

### Complete Simulation Cycle
```
┌─────────────────────────────────────────────────────────────┐
│ SIMULATION STEP (delta_time = 1.0)                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Generate Traffic (Poisson arrivals)                     │
│    - Time-of-day multipliers (rush hour patterns)          │
│    - Random variation (±15%)                               │
│    - Add to queues                                         │
│                                                             │
│ 2. Determine Green Directions                             │
│    - Based on current_phase (NS_GREEN, EW_GREEN, etc.)    │
│                                                             │
│ 3. Discharge Traffic                                       │
│    - Green directions discharge at saturation_flow         │
│    - Track vehicles_discharged for throughput             │
│                                                             │
│ 4. Get Current Vehicle Counts                             │
│    - Read from simulator queues                            │
│                                                             │
│ 5. Update Controller                                       │
│    - update_vehicle_counts(n,s,e,w)                        │
│      ├── Store previous counts                             │
│      ├── Update arrival rates (EMA learning)              │
│      └── Recalculate green times for NS and EW            │
│                                                             │
│ 6. Advance Traffic Light                                   │
│    - controller.update(delta_time)                         │
│      ├── Advance elapsed time                              │
│      ├── Check for extensions (get_extension_time)        │
│      ├── Compare pressures if in green phase              │
│      ├── If time's up: record duration, transition        │
│      └── Return current (or new) phase                    │
│                                                             │
│ 7. Record History                                          │
│    - Timestamps, phases, queues, green times, metrics     │
│                                                             │
│ 8. Update Visualization (if enabled)                       │
│    - visualizer.update(step, result, status)              │
└─────────────────────────────────────────────────────────────┘
```

### Controller Update Deep Dive
```
update_vehicle_counts(n,s,e,w):
    1. Save previous counts (for arrival calculation)
    2. Update vehicle_counts dict
    3. For each direction:
       - arrivals = max(0, current - previous)
       - if arrivals > 0:
           arrival_rate = 0.7×old + 0.3×arrivals  (EMA, α=0.3)
    4. Recalculate phase_timings:
       - NS_GREEN = _calculate_green_time('north','south')
       - EW_GREEN = _calculate_green_time('east','west')

_calculate_green_time(dir1, dir2):
    total = vehicle_counts[dir1] + vehicle_counts[dir2]
    if total == 0: return min_green_time
    
    base = min_green_time
    extension = min(total × extension_per_vehicle, max_extension)
    
    # Balancing: if this direction has >30% more than opposite
    other = sum of opposite direction queues
    if other > 0 and total/other > 1.3:
        imbalance = (total/other - 1.0) × 0.8
        balance_ext = min(imbalance × total × 0.3, max_extension×0.4)
        extension += balance_ext
    elif other == 0 and total > 0:
        extension += min(total × 0.2, max_extension×0.3)
    
    return base + extension + gap_time  # clamped to [min, max]

_get_next_phase():
    if in GREEN phase and elapsed >= min_green_time:
        ns_pressure = _calculate_pressure('north','south')
        ew_pressure = _calculate_pressure('east','west')
        
        if current == NS_GREEN and ew_pressure > ns_pressure × 1.2:
            return NS_YELLOW  # Switch to give EW green
        if current == EW_GREEN and ns_pressure > ew_pressure × 1.2:
            return EW_YELLOW  # Switch to give NS green
    
    # Default: advance in fixed sequence
    return next phase in [NS_GREEN, NS_YELLOW, ALL_RED, EW_GREEN, EW_YELLOW, ALL_RED]
```

## Class Relationships

### Advanced System (Individual Direction)

```
┌─────────────────────────────────────────────────────────────┐
│                AdvancedTrafficSimulator                      │
│  - queues: Dict (north, south, east, west)                 │
│  - arrival_rate, saturation_flow                           │
│  - history: Dict (per-direction tracking)                  │
│  - controller: AdvancedTrafficController                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ has-a
                            ▼
┌─────────────────────────────────────────────────────────────┐
│             AdvancedTrafficController                        │
│  - config: AdvancedTrafficConfig                            │
│  - current_phase, current_phase_elapsed                     │
│  - vehicle_counts: Dict (4 directions)                      │
│  - arrival_rates: Dict (4 directions)                       │
│  - phase_timings: Dict (9 phases)                           │
│  - phase_history: List (last 10 directions)                 │
│  - actual_phase_durations: List                             │
│  - total_vehicles_processed: int                            │
│  - direction_vehicles_processed: Dict                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              TrafficVisualizer (optional)                   │
│  - simulator: AdvancedTrafficSimulator OR SimpleTrafficSimulator │
│  - 6 axes for real-time plotting                           │
│  - data arrays for all metrics                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           AdvancedTrafficConfig (dataclass)                  │
│  - Individual direction timing parameters                  │
│  - Fairness and pressure parameters                        │
└─────────────────────────────────────────────────────────────┘
```

### Original System (Paired Directions)

```
┌─────────────────────────────────────────────────────────────┐
│                 SimpleTrafficSimulator                       │
│  - queues: Dict (north, south, east, west)                 │
│  - arrival_rate, saturation_flow                           │
│  - history: Dict                                           │
│  - controller: TrafficLightController                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ has-a
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                TrafficLightController                        │
│  - config: EnhancedTrafficLightConfig                       │
│  - current_phase, current_phase_elapsed                     │
│  - vehicle_counts: Dict (4 directions)                      │
│  - arrival_rates: Dict (4 directions)                       │
│  - phase_timings: Dict (6 phases)                           │
│  - actual_phase_durations: List                             │
│  - total_vehicles_processed: int                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           EnhancedTrafficLightConfig (dataclass)             │
│  - Paired direction timing parameters                      │
│  - Traffic and adaptive parameters                         │
└─────────────────────────────────────────────────────────────┘
```

## Algorithm Deep Dive: Max-Pressure Control (Individual Direction)

### Pressure Calculation (Per Direction)
```
Pressure(direction) = (Queue_Length^0.7) × max(Arrival_Rate, 0.3)
```

**Why this works:**
- Queue length = current demand (vehicles waiting now)
- Arrival rate = expected future demand (vehicles arriving during red)
- Queue^0.7 provides diminishing returns (prevents monopoly by very long queues)
- Minimum arrival rate of 0.3 prevents zero-pressure scenarios
- Higher pressure = more urgent need for green

**Fairness Penalties Applied:**
1. **Just served**: If this direction was last green, multiply by 0.5 (50% reduction)
2. **Recent history**: For each appearance in last 10 phases, apply penalty factor `1.0 - 0.4/(i+2)` where i is position in reversed history (0 = most recent)

**Example:**
```
Direction North: queue=15, arrival_rate=1.2
Base pressure = 15^0.7 × 1.2 = 6.1 × 1.2 = 7.3

If North was just served: 7.3 × 0.5 = 3.7
If North was 2nd most recent in history: 7.3 × (1.0 - 0.4/3) = 7.3 × 0.87 = 6.3
```

### Green Time Calculation (Per Direction)
```
Base = min_green_time
Vehicle_extension = min(vehicles × extension_per_vehicle, max_extension)

If pressure_ratio > 1.5:
    # This direction has >50% higher pressure than average of others
    pressure_extension = min((pressure_ratio - 1.0) × 5.0, max_extension × 0.3)
    Green_Time += pressure_extension

Green_Time += gap_time
Green_Time = clamp(Green_Time, min_green_time, max_green_time)
```

**Components Explained:**
- **Base minimum**: Ensures minimum service time (e.g., 10s)
- **Vehicle extension**: `min(queue × 0.8, 25s)` - scales with backlog
- **Pressure extension**: Extra time if this direction is significantly more urgent (pressure >150% of others)
- **Gap time**: Safety clearance (e.g., 2s)

**Example:**
```
North: 20 vehicles, pressure_ratio = 2.1
Base = 10s
Vehicle ext = min(20 × 0.8, 25) = 16s
Pressure ext = min((2.1-1.0)×5.0, 25×0.3) = min(5.5, 7.5) = 5.5s
Gap = 2s
Total = 10 + 16 + 5.5 + 2 = 33.5s (clamped to max 45s)
```

### Phase Selection Algorithm

The system uses a **dynamic priority-based** approach rather than fixed sequence:

**During GREEN/YELLOW phases:**
- Continue until minimum green time served
- Check for early transition if other directions become more urgent
- Force transition after `base_green + max_extension`

**During ALL_RED phase (decision point):**
1. Calculate pressure for all 4 directions (with fairness penalties)
2. Apply additional recency penalties based on phase history
3. Select direction with highest adjusted pressure
4. Return corresponding GREEN phase

**Recency Penalty in Selection:**
```python
for i, direction in enumerate(reversed(phase_history)):
    age_factor = 1.0 / (i + 2)  # 0.5, 0.33, 0.25, ...
    pressures[direction] *= (1.0 - 0.3 × age_factor)  # Up to 30% reduction
```

This ensures directions that were served recently are less likely to be selected immediately again.

### Extension Logic During Green

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

### Phase Sequence (Dynamic)

Unlike the fixed 6-phase cycle of the paired system, the individual direction system has a **variable sequence**:

```
ALL_RED → (select highest pressure direction) → GREEN → YELLOW → ALL_RED → repeat
```

The order of directions served depends entirely on traffic conditions. However, the system maintains a minimum of `min_phase_cycle` (default 2) cycles before the same direction can be selected again, preventing rapid oscillation.

**Typical Pattern:**
- Heavy North: N → S → E → W → N (if North remains heavy)
- Balanced: Random order based on slight pressure differences
- Asymmetric: Serves heavy directions more frequently, but all get service

### Comparison to Paired System

| Aspect | Paired (NS/EW) | Individual (N/S/E/W) |
|--------|----------------|---------------------|
| Phases | 6 fixed phases | 9 phases, dynamic order |
| Pressure calc | (N+S) × rate | N^0.7 × rate (individual) |
| Fairness | Between pairs | Between all 4 directions |
| Flexibility | Medium | High |
| Complexity | Lower | Higher |
| Efficiency | 65-75% | 70-80% |

## Performance Metrics System

### Metrics Tracked
| Metric | Calculation | Access Path |
|--------|-------------|-------------|
| Efficiency | green_time / total_cycle_time × 100 | status['performance']['efficiency'] |
| Throughput | vehicles_processed / total_time × 60 | status['performance']['vehicle_throughput'] |
| Average Green Time | mean of actual_phase_durations for GREEN phases | status['performance']['average_green_time'] |
| Remaining Time | phase_timings[current] - elapsed | status['remaining_time'] |
| Pressure | (queue_sum) × (avg_arrival_rate) | Computed in visualizer |
| Queue Balance | (N+S) - (E+W) | Computed in visualizer |
| Cumulative Throughput | controller.total_vehicles_processed | visualizer.cumulative_throughput |

### History Structure (SimpleTrafficSimulator)
```python
self.history = {
    'timestamps': [t0, t1, ...],
    'phases': ['NS_GREEN', ...],
    'queues': {
        'north': [q0, q1, ...],
        'south': [...],
        'east': [...],
        'west': [...]
    },
    'green_durations': {
        'ns': [duration_when_NS_green, ...],
        'ew': [...]
    },
    'performance': {
        'timestamps': [...],
        'efficiency': [...],
        'throughput': [...]
    }
}
```

## Simulation Workflow

### Initialization
1. Create config (EnhancedTrafficLightConfig or custom)
2. Instantiate SimpleTrafficSimulator(config)
3. (Optional) Create TrafficVisualizer(simulator)
4. Initialize history arrays

### Main Loop
```python
for step in range(num_steps):
    # 1. Update simulation (1 second per step typically)
    result = sim.update(delta_time=1.0)
    
    # 2. Get status
    status = sim.controller.get_status()
    
    # 3. Display (terminal or graphical)
    if visualizer:
        visualizer.update(step, result, status)
    else:
        print_metrics(step, status, sim.queues)
    
    # 4. Sleep for real-time pacing (optional)
    time.sleep(0.2)  # 200ms between steps
```

### Termination
1. Loop exits (steps complete or user interrupt)
2. Print summary statistics
3. If visualizer: call visualizer.final_plot() to show final charts
4. Access sim.history for custom analysis

## Error Handling and Validation

### Configuration Validation
The code does not have explicit validation but relies on Python's type hints and runtime errors. Recommended additions:
```python
def validate_config(config):
    assert config.min_green_time > 0
    assert config.max_green_time >= config.min_green_time
    assert config.yellow_time > 0
    assert config.all_red_time > 0
    assert config.extension_per_vehicle >= 0
    assert config.max_extension >= 0
    assert config.gap_time >= 0
    assert config.arrival_rate >= 0
    assert config.saturation_flow >= 0
```

### Robustness Features
- **Clamping**: Green times clamped to [min_green_time, max_green_time]
- **Minimum service**: Even with zero vehicles, returns min_green_time
- **Division protection**: Uses max(avg_rate, 0.5) to avoid zero pressure
- **NaN handling**: Visualizer filters NaN for green time scatter plots

## Extensibility Points

### 1. Replace Traffic Generation
```python
class RealTrafficSimulator(SimpleTrafficSimulator):
    def generate_traffic(self, delta_time):
        # Fetch from camera/API
        counts = get_real_vehicle_counts()
        for direction in ['north','south','east','west']:
            self.queues[direction] += counts[direction]
```

### 2. Add Emergency Vehicle Priority
```python
# In TrafficLightController._get_next_phase():
if self.emergency_vehicle_present:
    # Force green for emergency direction
    if emergency_direction in ['north','south']:
        return LightPhase.NORTH_SOUTH_GREEN
    else:
        return LightPhase.EAST_WEST_GREEN
```

### 3. Multi-Intersection Coordination
```python
class NetworkController:
    def __init__(self, intersections):
        self.intersections = intersections  # List of TrafficLightController
    
    def coordinate(self):
        # Adjust green times based on upstream/downstream queues
        # Implement green wave or offset optimization
```

### 4. Custom Pressure Function
```python
class CustomController(TrafficLightController):
    def _calculate_pressure(self, dir1, dir2):
        # Include wait time, queue variance, etc.
        base_pressure = super()._calculate_pressure(dir1, dir2)
        wait_time_penalty = self._calculate_wait_time_penalty()
        return base_pressure + wait_time_penalty
```

## Testing Strategy

### Unit Tests (to be implemented)
```python
def test_green_time_calculation():
    config = EnhancedTrafficLightConfig()
    controller = TrafficLightController(config)
    controller.vehicle_counts = {'north': 10, 'south': 5, 'east': 0, 'west': 0}
    green_time = controller._calculate_green_time('north','south')
    assert green_time >= config.min_green_time
    assert green_time <= config.max_green_time

def test_pressure_calculation():
    controller = TrafficLightController()
    controller.vehicle_counts = {'north': 20, 'south': 10, 'east': 5, 'west': 5}
    controller.arrival_rates = {d: 1.0 for d in ['north','south','east','west']}
    ns_pressure = controller._calculate_pressure('north','south')
    assert ns_pressure == 30.0  # (20+10) × 1.0
```

### Integration Tests
- Run full simulation with known traffic pattern
- Verify phase transitions occur
- Check metrics are computed correctly
- Validate history recording

### Performance Tests
- 10,000 step simulation measures execution time
- Memory usage profiling
- Visualization update rate (target: >10 FPS)

## Deployment Considerations

### Hardware
- **Development**: Any modern PC/laptop
- **Production**: Raspberry Pi 4 or similar (for edge deployment)
- **Sensors**: 4 cameras with vehicle detection (or loop detectors)
- **Network**: Optional, for remote monitoring

### Software
- **Python**: 3.8+ (tested on 3.9-3.11)
- **Dependencies**: numpy, matplotlib
- **OS**: Linux (Raspberry Pi OS), Windows, macOS

### Installation
```bash
# Clone or extract project
cd traffic_simulation
pip install -r requirements.txt

# Run tests (when implemented)
pytest tests/

# Start simulation
python simple_simulation.py
# or
python visualize.py
```

### Maintenance
- **Parameter tuning**: Adjust config for specific intersection characteristics
- **Logging**: Add file logging for long-term monitoring
- **Updates**: Replace traffic_light_controller.py with improved algorithm
- **Calibration**: Validate arrival_rate and saturation_flow against real data

## Future Enhancements

### 1. Pedestrian Integration
- Add pedestrian buttons/requests
- All-red phase extensions for crossing
- Pedestrian countdown timers

### 2. Multi-Intersection Coordination
- Green wave for platoons
- Offset optimization
- Network-wide pressure calculation

### 3. Machine Learning
- Predict arrival rates from historical patterns
- Reinforcement learning for parameter optimization
- Anomaly detection (accidents, special events)

### 4. Real-Time API
- REST endpoint for status
- WebSocket for live updates
- Configuration hot-reload

### 5. Advanced Analytics
- Queue length prediction
- Travel time estimation
- Emissions calculation

## Conclusion

The architecture provides a clean separation between control logic, simulation, and visualization. The max-pressure algorithm is implemented clearly in `TrafficLightController` with well-defined methods. The system is readily extensible for real-world deployment with actual vehicle detection systems, and the comprehensive visualization enables deep analysis and parameter tuning.