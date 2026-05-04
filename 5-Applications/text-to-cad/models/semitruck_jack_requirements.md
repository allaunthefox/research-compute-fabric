# Semitruck Jack Requirements and Design Specifications

## Application Context
- **Target**: Semitruck lifting jack for maintenance operations
- **Primary Use**: Tire changes, under-vehicle maintenance, trailer leveling
- **Operating Environment**: Roadside, service centers, warehouses
- **Safety Critical**: Failure can cause injury/death and property damage

## Performance Requirements

### Load Capacity
- **Minimum**: 20 tons (44,000 lbs / 19,600 kg)
- **Target**: 50 tons (110,000 lbs / 49,900 kg)
- **Maximum**: 100 tons (220,000 lbs / 99,800 kg)
- **Load Types**: Static (parked), dynamic (minor movement during lift)

### Lift Height
- **Minimum Lift**: 12 inches (305 mm)
- **Target Lift**: 18 inches (457 mm)
- **Maximum Lift**: 24 inches (610 mm)
- **Adjustable**: Multiple height positions preferred

### Stability Requirements
- **Safety Factor**: 3.0 minimum (heavy equipment standard)
- **Target Safety Factor**: 4.0 (for critical applications)
- **Lateral Stability**: Must resist 15° tilt
- **Base Stability**: Wide footprint, low center of gravity
- **Locking Mechanism**: Mechanical lock at each height position

## Geometry Constraints

### Overall Dimensions
- **Maximum Height (retracted)**: 24 inches (610 mm)
- **Maximum Base Width**: 30 inches (762 mm)
- **Maximum Base Length**: 40 inches (1016 mm)
- **Maximum Weight**: 100 lbs (45 kg) for portability

### Manifold Design Constraints
- **Topology**: 3D manifold structure (not merkle tree)
- **Load Paths**: Multiple load-bearing paths for redundancy
- **Strain Distribution**: FAMM frustration-driven load sharing
- **Curvature**: Manifold-generalized Bernoulli optimization
- **Scale**: Macro-scale (centimeters to meters, not millimeters)

## Material Considerations

### Material Options
1. **Steel** (Standard for heavy jacks)
   - Yield strength: 250-400 MPa
   - Young's modulus: 200 GPa
   - Density: 7850 kg/m³
   - Manufacturing: Welded, forged, or machined

2. **SLS Metal** (Additive manufacturing option)
   - Materials: Stainless steel 316L, titanium, aluminum
   - Yield strength: 200-500 MPa (material dependent)
   - Porosity: 2-5%
   - Anisotropy: Present (build direction dependent)

3. **Hybrid** (SLS polymer + steel reinforcement)
   - SLS nylon PA12 for complex geometry
   - Steel inserts for load-bearing paths
   - Bonding: Mechanical interlock, adhesive

### Recommended Material
**Steel** for initial design (proven reliability, no SLS limitations at this scale)
- Consider SLS metal for complex manifold features
- Hybrid approach for optimization

## Research Stack Mathematics Integration

### FAMM Frustration Physics
- **Application**: Stress redistribution across manifold
- **Goal**: Minimize frustration to prevent stress concentrations
- **Implementation**: Load sharing between parallel load paths

### Manifold-Generalized Bernoulli
- **Application**: Optimal load distribution on curved manifold surfaces
- **Equation**: P + ½ρv² + ρgh + ∫κ ds = constant
- **Goal**: Balance pressure/velocity across manifold topology

### String-Star Manifold
- **Application**: Curvature-aware geometry optimization
- **Goal**: Information conservation in strain propagation
- **Implementation**: Curvature-based adaptation

### Scale Space
- **Application**: Multi-scale optimization from micro to macro
- **Goal**: Find optimal geometry across different scale representations
- **Implementation**: Scale-space evolution of manifold topology

## OSHA Compliance Requirements

### OSHA 1926.305 (Construction Industry) - Jacks
**Standard Reference**: 29 CFR § 1926.305

**Key Requirements:**
- **(a)(1) Rated Capacity**: Must be legibly marked on all jacks and shall not be exceeded
- **(a)(2) Positive Stop**: All jacks shall have a positive stop to prevent overtravel
- **(c) Blocking**: Base must be blocked/cribbed when firm foundation needed; wood block between cap and load if slippage possible
- **(d)(1)(i) Load Securing**: After load raised, must be cribbed, blocked, or otherwise secured at once
- **(d)(1)(ii) Freezing Protection**: Hydraulic jacks exposed to freezing temperatures must have adequate antifreeze liquid
- **(d)(1)(iii) Lubrication**: All jacks must be properly lubricated at regular intervals
- **(d)(1)(iv) Inspection Schedule**:
  - Constant/intermittent use at one locality: once every 6 months
  - Jacks sent out for special work: when sent out and when returned
  - Jack subjected to abnormal load or shock: immediately before and after
- **(d)(1)(v) Parts Inspection**: Repair or replacement parts must be examined for possible defects
- **(d)(1)(vi) Tagging**: Out-of-order jacks must be tagged and shall not be used until repairs made

### OSHA 1910.244 (General Industry) - Other Portable Tools and Equipment
**Standard Reference**: 29 CFR § 1910.244(a)

**Key Requirements:**
- **(a)(1)(i) Operator Responsibility**: Operator must ensure jack has rating sufficient to lift and sustain load
- **(a)(1)(ii) Marking**: Rated load must be legibly and permanently marked in prominent location by casting, stamping, or other suitable means
- **(a)(2)(i) Blocking**: In absence of firm foundation, base must be blocked; wood block between cap and load if slippage possible
- **(a)(2)(ii) Stop Indicator**: Operator must watch stop indicator (kept clean) to determine travel limit; limit shall not be overrun
- **(a)(2)(iii) Load Securing**: After load raised, must be cribbed, blocked, or otherwise secured at once
- **(a)(2)(iv) Freezing Protection**: Hydraulic jacks exposed to freezing temperatures must be supplied with adequate antifreeze liquid
- **(a)(2)(v) Lubrication**: All jacks must be properly lubricated at regular intervals
- **(a)(2)(vi) Inspection Schedule** (same as 1926.305)
- **(a)(2)(vii) Parts Inspection**: Repair or replacement parts must be examined for possible defects
- **(a)(2)(viii) Tagging**: Out-of-order jacks must be tagged and shall not be used until repairs made

### Design Compliance Checklist
- [ ] Rated capacity marked legibly and permanently (casting/stamping)
- [ ] Positive stop mechanism to prevent overtravel
- [ ] Stop indicator visible and cleanable
- [ ] Blocking points on base for firm foundation
- [ ] Anti-slip cap design or wood block provision
- [ ] Load securing points (cribbing/blocking attachment)
- [ ] Antifreeze compatibility for hydraulic systems
- [ ] Lubrication points accessible for regular maintenance
- [ ] Inspection checklist and tag provision

## Safety Goals

### Primary Safety Metrics
1. **Yield Safety Factor**: ≥ 3.0 (OSHA requires rated capacity not exceeded)
2. **Buckling Safety Factor**: ≥ 2.5
3. **Fatigue Life**: ≥ 10,000 cycles at rated load
4. **Stability Safety Factor**: ≥ 2.0 (lateral)

### Failure Mode Prevention
- **Yield**: Prevent plastic deformation under rated load
- **Buckling**: Prevent column buckling under compression
- **Fatigue**: Prevent crack propagation from cyclic loading
- **Instability**: Prevent tipping or lateral collapse

### Redundancy
- **Load Paths**: Minimum 3 independent load paths
- **Locking**: Mechanical lock + hydraulic check valve
- **Failure Mode**: Graceful degradation (not catastrophic)

## Performance Goals

### Efficiency Metrics
1. **Lift Efficiency**: Input force to output force ratio
2. **Speed**: Time to full lift (target: < 60 seconds)
3. **Effort**: Maximum human effort to operate
4. **Durability**: Service life (target: 10+ years)

### Usability
- **Setup Time**: < 5 minutes
- **Operation**: Single person capable
- **Portability**: Can be moved by one person
- **Storage**: Compact when retracted

## Design Approach

### Phase 1: Requirements Analysis (Current)
- Define load cases and constraints
- Select material system
- Establish safety targets

### Phase 2: Manifold Topology Design
- Design 3D manifold structure
- Apply FAMM frustration minimization
- Optimize with manifold Bernoulli

### Phase 3: Physics Simulation
- Calculate stress distribution
- Verify safety factors
- Identify failure modes

### Phase 4: CAD Generation
- Create 3D model
- Generate STL for SLS (if applicable)
- Generate drawings for manufacturing

### Phase 5: Optimization
- Iterate on design based on simulation
- Target safety and performance goals
- Finalize specifications

## Success Criteria
- [ ] Safety factor ≥ 3.0 under all load cases
- [ ] Load capacity ≥ 50 tons
- [ ] Lift height ≥ 18 inches
- [ ] Weight ≤ 100 lbs
- [ ] Manufacturing feasible
- [ ] Cost-effective design
