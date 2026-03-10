# Code Architecture and Workflow Documentation

## System Overview

The smart traffic light simulator consists of a modular architecture with clear separation of concerns, enabling easy maintenance and extension.

## Core Components

### 1. TrafficLightController
**Location**: `traffic_light_controller.py`

**Purpose**: Main control logic for adaptive traffic light timing

**Key Features**:
- Vehicle-based timing adjustments
- Gap time integration
- Performance metrics tracking
- Emergency vehicle handling

**Main Methods**:
```python
def update(self, delta_time: float) -> LightPhase
    # Updates traffic light state based on elapsed time
    # Returns new phase if changed

def update_vehicle_counts(self, north, south, east, west)
    # Updates vehicle counts from detection system

def get_status(self) -> Dict
    # Returns complete system status with metrics
```

### 2. SimpleTrafficSimulator
**Location**: `simple_simulation.py`

**Purpose**: Terminal-based simulation with visualization

**Key Features**:
- Real-time ASCII visualization
- Performance metrics display
- Step-by-step simulation control
- Comprehensive statistics tracking

**Main Methods**:
```python
def run(self, duration_seconds, step_interval)
    # Main simulation loop with visualization

def update(self, delta_time)
    # Executes one simulation step

def display_intersection(self, result)
    # Renders ASCII intersection display
```

### 3. Enhanced Configuration
**Location**: `enhanced_config.py`

**Purpose**: Centralized configuration management

**Key Features**:
- All timing parameters in one place
- Easy parameter adjustment
- Validation and defaults
- Extensible configuration structure

**Configuration Parameters**:
```python
@dataclass
class EnhancedTrafficLightConfig:
    min_green_time: float
    max_green_time: float
    vehicle_threshold: int
    extension_per_vehicle: float
    gap_time: float
    priority_boost: float
    # ... additional parameters
```

## Data Flow Architecture

### 1. Vehicle Detection Flow
```
Vehicle Detection System
        ↓
Update Vehicle Counts
        ↓
TrafficLightController.update_vehicle_counts()
        ↓
Timing Recalculation
        ↓
Phase Update Decision
```

### 2. Simulation Loop Flow
```
Simulation Step
        ↓
Generate Traffic
        ↓
Discharge Traffic
        ↓
Update Controller
        ↓
Phase Transition
        ↓
Display Update
        ↓
Metrics Recording
```

### 3. Performance Monitoring Flow
```
Real-time Metrics Collection
        ↓
Efficiency Calculation
        ↓
Throughput Measurement
        ↓
Queue Length Tracking
        ↓
Historical Data Storage
```

## Class Relationships

### Inheritance Hierarchy
```
EnhancedTrafficLightConfig (dataclass)
        ↓
TrafficLightController
        ↓
SimpleTrafficSimulator
```

### Composition Relationships
```
SimpleTrafficSimulator
    ├── TrafficLightController (has-a)
    ├── EnhancedTrafficLightConfig (uses)
    └── History Tracking (contains)
```

## Algorithm Implementation

### Timing Calculation Algorithm
```python
def _calculate_green_time(self, dir1, dir2):
    # Step 1: Calculate base time
    total_vehicles = self.vehicle_counts[dir1] + self.vehicle_counts[dir2]
    
    # Step 2: Apply vehicle extensions
    extension = min(total_vehicles * self.config.extension_per_vehicle,
                   self.config.max_extension)
    
    # Step 3: Add gap time
    gap_time = self.config.gap_time * total_vehicles
    
    # Step 4: Calculate final time
    adaptive_time = self.config.min_green_time + extension + gap_time
    
    # Step 5: Apply bounds
    return max(self.config.min_green_time,
              min(adaptive_time, self.config.max_green_time))
```

### Phase Transition Logic
```python
def update(self, delta_time):
    # Step 1: Advance time
    self.current_phase_elapsed += delta_time
    
    # Step 2: Check for extensions
    if self.current_phase in [NS_Green, EW_Green]:
        extension = self.get_extension_time()
        if extension > 0:
            current_duration += extension
    
    # Step 3: Check for phase change
    if self.current_phase_elapsed >= current_duration:
        # Record duration
        self.actual_phase_durations.append({
            'phase': self.current_phase.value,
            'duration': self.current_phase_elapsed
        })
        
        # Transition to next phase
        self.current_phase = self._get_next_phase()
        self.current_phase_elapsed = 0.0
    
    return self.current_phase
```

## Performance Metrics System

### Efficiency Calculation
```python
def _calculate_efficiency(self):
    # Calculate green time vs total cycle time
    total_time = sum(d['duration'] for d in self.actual_phase_durations)
    green_time = sum(d['duration'] for d in self.actual_phase_durations 
                    if 'GREEN' in d['phase'])
    return (green_time / total_time) * 100 if total_time > 0 else 0.0
```

### Throughput Measurement
```python
def _calculate_vehicle_throughput(self):
    # Calculate vehicles processed per minute
    total_vehicles = sum(self.vehicle_counts.values())
    total_time = sum(d['duration'] for d in self.actual_phase_durations)
    return (total_vehicles / total_time) * 60 if total_time > 0 else 0.0
```

## Simulation Workflow

### Initialization Phase
1. Load configuration parameters
2. Initialize traffic light controller
3. Set up simulation environment
4. Prepare data structures

### Main Simulation Loop
1. Generate new traffic arrivals
2. Discharge traffic from green directions
3. Update vehicle counts
4. Calculate adaptive timings
5. Execute phase transitions
6. Update visualization
7. Record performance metrics

### Termination Phase
1. Calculate final statistics
2. Generate analysis reports
3. Save historical data
4. Clean up resources

## Error Handling and Validation

### Input Validation
```python
def validate_config(config):
    # Check timing parameters
    assert config.min_green_time > 0
    assert config.max_green_time > config.min_green_time
    assert config.yellow_time > 0
    
    # Check vehicle parameters
    assert config.vehicle_threshold >= 0
    assert config.extension_per_vehicle >= 0
    assert config.max_extension >= 0
    
    # Check performance parameters
    assert config.priority_boost >= 1.0
```

### Runtime Error Handling
```python
def safe_update(self, delta_time):
    try:
        return self.update(delta_time)
    except Exception as e:
        # Log error
        print(f"Error in update: {e}")
        # Return current phase to maintain stability
        return self.current_phase
```

## Extensibility Points

### 1. Vehicle Detection Integration
```python
# Current: Simulated vehicle counts
# Future: Real camera feed integration
# Interface: update_vehicle_counts() method
```

### 2. Advanced Traffic Patterns
```python
# Current: Poisson arrival process
# Future: Machine learning-based prediction
# Interface: generate_traffic() method
```

### 3. Priority Systems
```python
# Current: Emergency vehicle priority
# Future: Public transport priority, pedestrian priority
# Interface: should_extend_current_phase() method
```

### 4. Performance Analytics
```python
# Current: Basic metrics
# Future: Advanced analytics, predictive modeling
# Interface: get_status() method
```

## Testing Strategy

### Unit Tests
- Configuration validation
- Timing calculation accuracy
- Phase transition logic
- Performance metric calculations

### Integration Tests
- Complete simulation workflow
- Vehicle detection integration
- Performance monitoring system
- Visualization accuracy

### Performance Tests
- Load testing with high traffic volumes
- Stress testing with rapid changes
- Scalability testing with multiple intersections

## Deployment Considerations

### Hardware Requirements
- Vehicle detection cameras
- Processing unit (Raspberry Pi or similar)
- Network connectivity
- Power supply

### Software Requirements
- Python 3.8+
- Required libraries (numpy, matplotlib)
- Operating system compatibility
- Network protocols

### Maintenance Requirements
- Regular software updates
- Hardware maintenance
- Performance monitoring
- Configuration adjustments

## Future Enhancements

### 1. Machine Learning Integration
- Predictive traffic pattern analysis
- Adaptive parameter optimization
- Anomaly detection

### 2. Cloud Connectivity
- Centralized traffic management
- Real-time data analytics
- Remote monitoring and control

### 3. Mobile Integration
- Driver notification system
- Real-time traffic updates
- Route optimization

### 4. IoT Sensor Integration
- Enhanced vehicle detection
- Environmental monitoring
- Pedestrian detection

## Conclusion

The codebase demonstrates a well-structured, modular approach to traffic light control with clear separation of concerns, comprehensive documentation, and extensibility for future enhancements.