# Smart Traffic Light Simulator

An advanced traffic light control system with **max-pressure adaptive timing algorithms** and comprehensive simulation capabilities. The system now features **individual direction control** for optimal traffic management.

## Features

### Core Algorithm (Advanced)
- **Individual Direction Control**: Treats N, S, E, W as separate directions
- **Max-Pressure Control**: Dynamically allocates green time based on traffic pressure (queue^0.7 × arrival rate)
- **Fairness Penalties**: Prevents starvation with recency-based pressure reduction
- **Adaptive Extensions**: Extends green phases based on vehicle count and pressure ratio
- **Realistic Discharge**: Models vehicle clearance with saturation flow rates

### Simulation Capabilities
- **Real-time Terminal Visualization**: ASCII intersection display with live metrics
- **Advanced Graphical Plots**: 6 interactive charts for deep analysis
- **Pressure Testing**: High-traffic load testing scenarios with countdown bars
- **Historical Tracking**: Comprehensive metrics storage for analysis

### Configuration
- **Fine-Tuned Parameters**: All timing and traffic parameters configurable
- **Realistic Patterns**: Time-of-day traffic variations with random fluctuations

## Quick Start

### Advanced Simulation (Individual Direction Control)
```bash
python advanced_simulation.py
```

### Advanced Controller Tests
```bash
python test_advanced_controller.py
python simple_advanced_test.py
```

## Configuration Parameters

### AdvancedTrafficConfig (Individual Direction Control)
**Used by**: `advanced_simulation.py`, `advanced_traffic_controller.py`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_green_time` | 10.0 s | Minimum green light duration per direction |
| `max_green_time` | 45.0 s | Maximum green light duration per direction |
| `yellow_time` | 3.0 s | Yellow light duration |
| `all_red_time` | 2.0 s | All-red clearance interval |
| `vehicle_threshold` | 3 | Minimum vehicles to consider extension |
| `extension_per_vehicle` | 0.8 s | Seconds added per vehicle |
| `max_extension` | 25.0 s | Maximum extension beyond base time |
| `gap_time` | 2.0 s | Gap between last vehicle and phase end |
| `min_phase_cycle` | 2 | Minimum phases before returning to same direction |
| `pressure_threshold` | 1.2 | Pressure ratio threshold for switching |

## Algorithm: Max-Pressure Control (Individual Direction)

The advanced controller uses a sophisticated max-pressure algorithm with individual direction control:

### Pressure Calculation (Per Direction)
```
Pressure(direction) = (Queue_Length^0.7) × max(Arrival_Rate, 0.3)
```

**Key differences from old system:**
- Uses **individual directions** (N, S, E, W) not pairs (NS, EW)
- Applies **diminishing returns** with queue^0.7 (prevents monopoly)
- Includes **fairness penalties** for recently served directions
- Considers **recency** via phase history (up to 10 phases)

### Green Time Allocation (Per Direction)
```
Green_Time = min_green_time
           + min(vehicles × extension_per_vehicle, max_extension)
           + pressure_extension (if pressure_ratio > 1.5)
           + gap_time
```

**Components:**
- **Base**: `min_green_time` (e.g., 10s)
- **Vehicle extension**: `min(vehicles × 0.8, 25s)`
- **Pressure extension**: Extra if this direction has >50% higher pressure than average of others
- **Gap time**: Clearance interval (e.g., 2s)

### Phase Transition Logic
1. **Minimum Green**: Must serve at least `min_green_time`
2. **Extensions**: Dynamically calculated each update based on current conditions
3. **Maximum Enforcement**: Force transition after `base_green + max_extension`
4. **Fairness**: Recency penalties reduce pressure for recently served directions

### Fairness Mechanism
The algorithm prevents starvation through multiple mechanisms:
- **Recency penalty**: Recently served directions get 50% pressure reduction
- **Phase history**: Directions in last 10 phases get up to 30% penalty (older = less)
- **Pressure ratio**: Only extends if this direction's pressure significantly exceeds others
- **Minimum phase cycle**: Configurable minimum cycles before returning to same direction

### Phase Sequence (9-Phase Cycle)
1. NORTH_GREEN → 2. NORTH_YELLOW → 3. ALL_RED →
4. SOUTH_GREEN → 5. SOUTH_YELLOW → 6. ALL_RED →
7. EAST_GREEN → 8. EAST_YELLOW → 9. ALL_RED →
10. WEST_GREEN → 11. WEST_YELLOW → 12. ALL_RED (repeat)

**Note**: The actual sequence is dynamic based on pressure calculations. The system selects the next direction with highest adjusted pressure during ALL_RED phase.

## Performance

### Expected Improvements vs Fixed Timing
| Metric | Fixed Timing | Max-Pressure Adaptive | Improvement |
|--------|--------------|----------------------|-------------|
| Efficiency | 40-50% | 65-75% | +50% |
| Throughput | 1500-1800 veh/hr | 2200-2500 veh/hr | +45% |
| Wait Time | High | 30-40% reduction | -35% |

### Key Performance Indicators
- **Efficiency**: Green time / total cycle time (target >65%)
- **Throughput**: Vehicles processed per minute
- **Queue Balance**: Difference NS-EW near zero indicates fairness
- **Pressure Index**: Shows which direction needs service

## Usage Examples

### Basic Simulation
```python
from enhanced_config import EnhancedTrafficLightConfig
from simple_simulation import SimpleTrafficSimulator

config = EnhancedTrafficLightConfig()
sim = SimpleTrafficSimulator(config)
sim.run()
```

### Custom Configuration
```python
config = EnhancedTrafficLightConfig(
    min_green_time=10.0,
    max_green_time=45.0,
    arrival_rate=2.0,  # Heavy traffic
    saturation_flow=2.0
)
sim = SimpleTrafficSimulator(config)

for step in range(100):
    result = sim.update(delta_time=1.0)
    status = sim.controller.get_status()
    queues = sim.queues
    throughput = status['performance']['vehicle_throughput']
```

### Accessing Metrics
```python
status = sim.controller.get_status()
print(f"Phase: {status['current_phase']}")
print(f"Efficiency: {status['performance']['efficiency']:.1f}%")
print(f"Throughput: {status['performance']['vehicle_throughput']:.1f} veh/min")
print(f"Remaining: {status['remaining_time']:.1f}s")
```

## Project Structure

```
traffic_simulation/
├── advanced_traffic_controller.py  # Individual direction max-pressure controller
├── advanced_simulation.py          # Advanced simulation with individual control
├── test_advanced_controller.py    # Advanced controller test suite
├── simple_advanced_test.py        # Simple advanced controller test
├── requirements.txt               # Dependencies (numpy, matplotlib)
├── README.md                      # This file
├── CODE_WORKFLOW.md               # Architecture & data flow
├── TIMING_ALGORITHM.md            # Algorithm deep dive
├── EFFICIENCY_ANALYSIS.md         # Performance analysis
└── ADVANCED_SYSTEM.md             # Advanced system documentation
```

## Understanding the Algorithm

### How Max-Pressure Works (Individual Direction)

1. **Calculate pressure** for each direction: `pressure = (queue^0.7) × max(arrival_rate, 0.3)`
2. **Apply fairness penalties**: Reduce pressure for recently served directions (50% if just served, up to 30% for older phases)
3. **Select next green**: Choose direction with highest adjusted pressure
4. **Calculate green time**: Base + vehicle extension + pressure extension (if ratio > 1.5) + gap
5. **Monitor continuously**: Check for early transition if other directions become more urgent
6. **Enforce fairness**: Phase history prevents any direction from being starved

### Why It's Effective
- **Predictive**: Uses arrival rate to anticipate future demand
- **Fair**: Recency penalties and phase history prevent indefinite starvation
- **Adaptive**: Learns arrival rates over time (EMA with α=0.3)
- **Efficient**: Only extends when necessary, bounded by max_extension
- **Individual**: Treats each direction separately for optimal allocation

### Parameter Effects
| Parameter | Increase → | Decrease → |
|-----------|------------|------------|
| `min_green_time` | Longer minimum service, fewer transitions | Quicker transitions, more overhead |
| `max_green_time` | Longer maximum green, better for heavy traffic | Shorter cycles, more frequent switching |
| `extension_per_vehicle` | More responsive to queues, longer greens | Less responsive, quicker transitions |
| `vehicle_threshold` | Extensions only for longer queues | Extensions for shorter queues |
| `gap_time` | More safety clearance, longer greens | Less clearance, shorter greens |

## Troubleshooting

### Queues growing without bound
**Cause**: Green time too short for traffic volume  
**Solution**: Increase `max_green_time` or `extension_per_vehicle`

### One direction always has long queues
**Cause**: Insufficient balancing or threshold too high  
**Solution**: Decrease `vehicle_threshold` or increase `max_extension`

### Too many phase transitions (short cycles)
**Cause**: Extensions too small or threshold too low  
**Solution**: Increase `min_green_time` or decrease `extension_per_vehicle`

### Low efficiency (<50%)
**Cause**: Too much green time on empty directions  
**Solution**: Decrease `min_green_time` or increase `vehicle_threshold`

## Future Enhancements

- [ ] **Machine Learning**: Predictive traffic pattern analysis
- [ ] **Real Detection**: Integration with actual camera feeds
- [ ] **Multi-Intersection**: Coordination across networks
- [ ] **Emergency Priority**: Special handling for emergency vehicles
- [ ] **Pedestrian Signals**: Integration with crosswalk signals
- [ ] **API Interface**: REST API for external control

## Documentation

- **CODE_WORKFLOW.md** - Architecture, data flow, class relationships
- **TIMING_ALGORITHM.md** - Detailed algorithm explanation with examples
- **EFFICIENCY_ANALYSIS.md** - Performance metrics and comparisons
