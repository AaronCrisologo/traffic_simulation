# Code Architecture and Workflow Documentation

## System Overview

The traffic simulator implements a **max-pressure adaptive control algorithm** with modular architecture for easy maintenance and extension. The system separates concerns into distinct components: control logic, simulation engine, visualization, and configuration.

## Core Components

### 1. TrafficLightController
**Location**: `traffic_light_controller.py`

**Purpose**: Max-pressure adaptive traffic light control

**Key Features**:
- Pressure-based phase decisions (queue × arrival rate)
- Queue balancing to prevent starvation
- Dynamic green time calculation
- Arrival rate learning (exponential moving average)
- Performance metrics tracking

**Main Methods**:
```python
def update(self, delta_time: float) -> LightPhase
    # Advances simulation time, checks for phase transitions
    # Returns new phase if changed

def update_vehicle_counts(self, north, south, east, west)
    # Updates vehicle counts, recalculates timings, updates arrival rates

def get_status(self) -> Dict
    # Returns complete status: phase, timings, performance metrics

def _calculate_pressure(self, dir1, dir2) -> float
    # Calculates traffic pressure = (queue1+queue2) × avg_arrival_rate

def _calculate_green_time(self, dir1, dir2) -> float
    # Computes adaptive green time with balancing extension

def _get_next_phase(self) -> LightPhase
    # Max-pressure decision: switch if opposite pressure > 120% of current
```

### 2. SimpleTrafficSimulator
**Location**: `simple_simulation.py`

**Purpose**: Terminal-based simulation with ASCII visualization

**Key Features**:
- Poisson traffic generation with time-of-day patterns
- Saturation flow discharge modeling
- Real-time ASCII intersection display
- History recording for analysis
- Configurable via EnhancedTrafficLightConfig

**Main Methods**:
```python
def __init__(self, controller_config)
    # Initializes controller and simulation state

def generate_traffic(self, delta_time)
    # Generates arrivals using Poisson process with rush-hour cycles

def discharge_traffic(self, green_directions, delta_time)
    # Removes vehicles at saturation flow rate with random variation

def update(self, delta_time=1.0) -> Dict
    # Executes one simulation step, returns phase and queue state

def run(self, steps=200, delay=0.2)
    # Main loop with ASCII display and metrics
```

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

### 4. Enhanced Configuration
**Location**: `enhanced_config.py`

**Purpose**: Centralized configuration with all parameters

**Key Features**:
- Dataclass for type safety
- Sensible defaults
- All timing, adaptive, and traffic parameters in one place

**Configuration Parameters**:
```python
@dataclass
class EnhancedTrafficLightConfig:
    # Timing (seconds)
    min_green_time: float = 12.0
    max_green_time: float = 60.0
    yellow_time: float = 3.5
    all_red_time: float = 2.0
    
    # Adaptive control
    vehicle_threshold: int = 4
    extension_per_vehicle: float = 0.6
    max_extension: float = 15.0
    gap_time: float = 2.5
    
    # Traffic simulation
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

```
┌─────────────────────────────────────────────────────────────┐
│                    SimpleTrafficSimulator                    │
│  - queues: Dict                                           │
│  - arrival_rate, saturation_flow                          │
│  - history: Dict                                          │
│  - controller: TrafficLightController                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ has-a
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                TrafficLightController                       │
│  - config: TrafficLightConfig                              │
│  - current_phase, current_phase_elapsed                    │
│  - vehicle_counts: Dict                                    │
│  - arrival_rates: Dict                                     │
│  - phase_timings: Dict                                     │
│  - actual_phase_durations: List                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              TrafficVisualizer (optional)                   │
│  - simulator: SimpleTrafficSimulator                       │
│  - 6 axes for real-time plotting                           │
│  - data arrays for all metrics                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           EnhancedTrafficLightConfig (dataclass)            │
│  - All timing, adaptive, and traffic parameters           │
└─────────────────────────────────────────────────────────────┘
```

## Algorithm Deep Dive: Max-Pressure Control

### Pressure Calculation
```
Pressure(direction_pair) = (Queue1 + Queue2) × (ArrivalRate1 + ArrivalRate2)/2
```

**Why this works:**
- Queue length = current demand (vehicles waiting now)
- Arrival rate = expected future demand (vehicles arriving while red)
- Product = total expected vehicles during red period
- Higher pressure = more urgent need for green

### Green Time with Balancing
```
Base = min_green_time
Extension = min(total_vehicles × ext_per_veh, max_ext)

If (total_vehicles / opposite_vehicles) > 1.3:
    # This direction has >30% more traffic
    imbalance_factor = (ratio - 1.0) × 0.8
    balance_ext = min(imbalance_factor × total_veh × 0.3, max_ext×0.4)
    Extension += balance_ext

Green_Time = Base + Extension + gap_time
```

**Balancing effect:** If NS has 30 vehicles, EW has 10 (ratio=3.0):
- imbalance_factor = (3.0-1.0)×0.8 = 1.6
- balance_ext = min(1.6×30×0.3, 15×0.4) = min(14.4, 6) = 6 seconds extra
- NS gets additional time to catch up, promoting fairness

### Phase Transition Decision
```
After min_green_time has elapsed:
    Calculate ns_pressure, ew_pressure
    
    If current == NS_GREEN and ew_pressure > ns_pressure × 1.2:
        Transition to NS_YELLOW (give EW green)
    Elif current == EW_GREEN and ns_pressure > ew_pressure × 1.2:
        Transition to EW_YELLOW (give NS green)
    Else:
        Continue in current green phase (may extend further)
```

**120% threshold:** Prevents premature switching due to noise, but allows early switching when traffic builds significantly on red side.

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