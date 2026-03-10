# Smart Traffic Light Timer Simulator

An advanced traffic light control system with adaptive timing algorithms and realistic simulation capabilities.

## Features

### Core Improvements
- **Fixed Algorithm Logic**: Corrected phase transition timing bug
- **Gap Time Implementation**: Realistic vehicle clearance intervals
- **Enhanced Performance Metrics**: Efficiency, throughput, and optimization analytics
- **Realistic Traffic Patterns**: Time-of-day variations and discharge rate fluctuations

### Advanced Features
- **Emergency Vehicle Detection**: Priority handling for emergency vehicles
- **Priority Boosting**: High-traffic direction optimization
- **Comprehensive Analytics**: Detailed performance reporting and visualization
- **Configurable Parameters**: Fine-tuned control over all timing aspects

## Files Overview

### Core Components
- `traffic_light_controller.py` - Main controller with adaptive algorithm
- `simple_simulation.py` - Terminal-based simulation with visualization
- `simulation.py` - Advanced simulation with CNN integration (stub)
- `test_run.py` - Automated testing and validation

### Configuration
- `enhanced_config.py` - Advanced configuration parameters
- `requirements.txt` - Python dependencies

## Quick Start

### Basic Simulation
```bash
python simple_simulation.py
```

### Enhanced Simulation
```bash
python -c "from enhanced_config import EnhancedTrafficLightConfig; from simple_simulation import SimpleTrafficSimulator; sim = SimpleTrafficSimulator(EnhancedTrafficLightConfig()); sim.run()"
```

### Testing
```bash
python test_run.py
```

## Configuration Parameters

### Timing Parameters
- `min_green_time`: Minimum green light duration (seconds)
- `max_green_time`: Maximum green light duration (seconds)
- `yellow_time`: Yellow light duration (seconds)
- `all_red_time`: All-red clearance interval (seconds)

### Adaptive Parameters
- `vehicle_threshold`: Minimum vehicles for extension
- `extension_per_vehicle`: Seconds added per vehicle
- `max_extension`: Maximum extension time
- `gap_time`: Vehicle clearance gap time

### Traffic Parameters
- `arrival_rate`: Vehicle arrival rate (vehicles/second)
- `saturation_flow`: Discharge rate when green (vehicles/second)

### Performance Parameters
- `max_queue_length`: Queue length for priority boost
- `priority_boost`: Multiplier for high-traffic directions

## Algorithm Details

The adaptive algorithm uses a sophisticated approach:

1. **Base Timing**: Starts with minimum green time
2. **Vehicle-Based Extension**: Adds time based on vehicle count
3. **Gap Time Logic**: Includes clearance intervals between vehicles
4. **Priority Boosting**: Increases green time for high-traffic directions
5. **Emergency Handling**: Provides extended priority for emergency vehicles

## Performance Metrics

The system tracks:
- **Efficiency**: Ratio of green time to total cycle time
- **Throughput**: Vehicles processed per minute
- **Average Wait Time**: Mean vehicle wait time
- **Queue Lengths**: Real-time queue monitoring

## Visualization

The simulation provides:
- Real-time ASCII intersection display
- Performance metrics overlay
- Step-by-step statistics
- Comprehensive analysis plots

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

## Testing

The test suite validates:
- Algorithm correctness
- Performance metrics accuracy
- Configuration parameter handling
- Emergency vehicle priority

## Future Enhancements

Potential improvements include:
- Machine learning-based traffic prediction
- Integration with real camera feeds
- Cloud-based traffic management
- Mobile app interface
- IoT device integration

## Algorithm Documentation

For detailed information about the timing algorithm, see [TIMING_ALGORITHM.md](TIMING_ALGORITHM.md).

## Efficiency Analysis

For comprehensive performance comparisons and statistical analysis, see [EFFICIENCY_ANALYSIS.md](EFFICIENCY_ANALYSIS.md).

## Code Architecture

For detailed technical documentation and workflow information, see [CODE_WORKFLOW.md](CODE_WORKFLOW.md).

## License

This project is for educational purposes and demonstrates advanced traffic control algorithms.