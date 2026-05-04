# Unified Area Mapping

## Overview

The Research Stack is transitioning from many separate named quantities to four unified areas. This mapping documents how current system variables collapse into the four higher-order domains.

## Four Unified Areas

### 1. Burden Area (B)
**Definition**: Anything that measures what it costs to carry, reconcile, sort, or stabilize information.

**Subdomains**:
- Load
- Cost
- Attention
- Translation difficulty
- Memory strain
- Pacing mismatch
- Divergence pressure

### 2. Geometry Area (G)
**Definition**: Anything that measures shape, curvature, basin structure, gradient flow, resonance, or manifold mismatch.

**Subdomains**:
- Basins
- Manifolds
- Gradients
- Curvature
- Resonance
- Differential attractors
- Metric structure

### 3. Adaptation Area (A)
**Definition**: Anything that measures update, convergence, reorganization, pacing, or temporal sorting.

**Subdomains**:
- Sorting rate
- Pacing
- Convergence
- Revision
- Iterative update
- Learning rate
- Temporal dynamics

### 4. Protection Area (P)
**Definition**: Anything that measures thresholding, compression, defensive closure, avalanche, or rupture.

**Subdomains**:
- Compression
- Thresholding
- Overload
- Avalanche
- Defensive closure
- Collapse
- Criticality

## Variable Mapping Table

| Variable | Source Module | Current Structure | Unified Area | Rationale |
|----------|--------------|------------------|--------------|-----------|
| **cost** | Bind.lean | Metric.cost | Burden | Direct cost measurement |
| **costEstimate** | NIICore.lean | Capability.costEstimate | Burden | Estimated processing cost |
| **priority** | NIICore.lean | WorkItem.priority | Burden | Priority indicates load urgency |
| **kappaSquared** | NIICore.lean | WorkItem.kappaSquared | Geometry | Curvature coupling parameter |
| **kappaHierarchy** | NIICore.lean | WorkItem.kappaHierarchy | Geometry | Hierarchical encoding efficiency |
| **epsilonMutation** | NIICore.lean | WorkItem.epsilonMutation | Protection | Adaptive threshold (mutation rate) |
| **geometricEfficiency** | NIICore.lean | Capability.geometricEfficiency | Geometry | How well geometric ops are used |
| **torsionalStress** | NIICore.lean | FammNII.torsionalStress | Geometry | Σ² from manifold state |
| **interlockingEnergy** | NIICore.lean | FammNII.interlockingEnergy | Geometry | I_lock energy |
| **laplacianEnergy** | NIICore.lean | FammNII.laplacianEnergy | Geometry | Δϕ Hodge-Laplacian vibration energy |
| **phi_bind** | Bind.lean | BindGradient.phi_bind | Burden | Bind objective function (cost) |
| **grad_phi** | Bind.lean | BindGradient.grad_phi | Geometry | Gradient of objective |
| **laplacian_lb** | Bind.lean | BindGradient.laplacian_lb | Geometry | Laplacian of load balance |
| **scaling_param** | Bind.lean | BindGradient.scaling_param | Adaptation | s parameter for scaling |
| **learning_rate** | Bind.lean | BindGradient.learning_rate | Adaptation | μ learning rate |
| **w, x, y, z** | Bind.lean | Quaternion components | Geometry | Quaternion state (4D rotation) |
| **ammr** | Bind.lean | InformationTheoreticConstraints.ammr | Burden | Average Mean Mutual Rate (information flow) |
| **avmr** | Bind.lean | InformationTheoreticConstraints.avmr | Burden | Average Variance Mutual Rate (information variance) |
| **inputSize** | SemanticRGFlow.lean | DecimationOperator.inputSize | Burden | Size of input (load) |
| **outputSize** | SemanticRGFlow.lean | DecimationOperator.outputSize | Burden | Size of output (load) |
| **weights** | SemanticRGFlow.lean | DecimationOperator.weights | Geometry | Weight matrix structure |
| **bias** | SemanticRGFlow.lean | DecimationOperator.bias | Burden | Bias term (cost offset) |
| **preservesInvariants** | SemanticRGFlow.lean | DecimationOperator.preservesInvariants | Protection | Invariant preservation (defensive) |
| **coupling** | SemanticRGFlow.lean | BetaFunction.coupling | Geometry | Coupling constant g |
| **flowVel** | SemanticRGFlow.lean | BetaFunction.flowVel | Adaptation | β(g) = ∂g/∂ln(s) (rate of change) |
| **isFixedPoint** | SemanticRGFlow.lean | BetaFunction.isFixedPoint | Adaptation | Fixed point condition (convergence) |
| **center** | SemanticRGFlow.lean | SemanticAttractor.center | Geometry | Attractor center point |
| **basinRadius** | SemanticRGFlow.lean | SemanticAttractor.basinRadius | Geometry | Basin structure |
| **potential** | SemanticRGFlow.lean | SemanticAttractor.potential | Geometry | Semantic potential V(φ) |
| **isIFSSet** | SemanticRGFlow.lean | SemanticAttractor.isIFSSet | Protection | Invariant set membership |
| **mutualInfo** | SemanticRGFlow.lean | InformationConstraint.mutualInfo | Burden | Mutual information (information cost) |
| **threshold** | SemanticRGFlow.lean | InformationConstraint.threshold | Protection | Optimization threshold |
| **isOptimized** | SemanticRGFlow.lean | InformationConstraint.isOptimized | Adaptation | Optimization status (convergence) |
| **metric** | SemanticRGFlow.lean | LatentManifold.metric | Geometry | Riemannian metric |
| **dimension** | SemanticRGFlow.lean | LatentManifold.dimension | Geometry | Manifold dimension |
| **ricciCurvature** | SemanticRGFlow.lean | LatentManifold.ricciCurvature | Geometry | Ricci curvature |
| **dampingCoefficient** | FieldDamping.lean | DampingParameters.dampingCoefficient | Protection | Damping (compression) |
| **velocityThreshold** | FieldDamping.lean | DampingParameters.velocityThreshold | Protection | Velocity threshold |
| **accelerationThreshold** | FieldDamping.lean | DampingParameters.accelerationThreshold | Protection | Acceleration threshold |
| **dampingRate** | FieldDamping.lean | DampingParameters.dampingRate | Adaptation | Rate of damping application |
| **couplingStrength** | NeighborCoupling.lean | CouplingParameters.couplingStrength | Geometry | k in Laplacian |
| **couplingRadius** | NeighborCoupling.lean | CouplingParameters.couplingRadius | Geometry | Maximum distance for coupling |
| **couplingDecay** | NeighborCoupling.lean | CouplingParameters.couplingDecay | Geometry | Decay with distance |
| **lines** | SubagentOrchestrator.lean | Module.lines | Burden | Module size (load) |
| **hasTheorems** | SubagentOrchestrator.lean | Module.hasTheorems | Protection | Theorem presence (verification) |
| **hasEvals** | SubagentOrchestrator.lean | Module.hasEvals | Protection | Evaluation witnesses (verification) |
| **expertiseLevel** | SubagentOrchestrator.lean | DomainExpert.expertiseLevel | Adaptation | Expertise level (learning) |
| **coverage** | SubagentOrchestrator.lean | CodebaseExpert.coverage | Burden | Fraction analyzed (load) |
| **importGraphComplete** | SubagentOrchestrator.lean | CodebaseExpert.importGraphComplete | Protection | Graph completeness (verification) |
| **theoremCoverage** | SubagentOrchestrator.lean | CodebaseExpert.theoremCoverage | Protection | Theorem coverage (verification) |
| **hybridizationScore** | SubagentOrchestrator.lean | IntegrationAnalyst.hybridizationScore | Adaptation | Hybridization potential (adaptation) |
| **impactWeight** | SubagentOrchestrator.lean | PriorityScheduler.impactWeight | Burden | Impact weight (cost) |
| **effortWeight** | SubagentOrchestrator.lean | PriorityScheduler.effortWeight | Burden | Effort weight (cost) |
| **threshold** | SubagentOrchestrator.lean | PriorityScheduler.threshold | Protection | Minimum score threshold |
| **cores** | DistributedTraining.lean | NetworkNode.cores | Burden | Core count (resource load) |
| **ramGB** | DistributedTraining.lean | NetworkNode.ramGB | Burden | RAM (resource load) |
| **hasGPU** | DistributedTraining.lean | NetworkNode.hasGPU | Burden | GPU availability (resource) |
| **storageGB** | DistributedTraining.lean | NetworkNode.storageGB | Burden | Storage (resource load) |
| **totalCores** | DistributedTraining.lean | NetworkResources.totalCores | Burden | Total cores (resource) |
| **totalRAMGB** | DistributedTraining.lean | NetworkResources.totalRAMGB | Burden | Total RAM (resource) |
| **totalNodes** | DistributedTraining.lean | NetworkResources.totalNodes | Burden | Total nodes (resource) |
| **gpuNodes** | DistributedTraining.lean | NetworkResources.gpuNodes | Burden | GPU nodes (resource) |
| **weight** | DistributedTraining.lean | NodeAssignment.weight | Burden | Assignment weight (load) |
| **coresAllocated** | DistributedTraining.lean | NodeAssignment.coresAllocated | Burden | Allocated cores (resource) |
| **ramAllocatedGB** | DistributedTraining.lean | NodeAssignment.ramAllocatedGB | Burden | Allocated RAM (resource) |
| **naturalLanguageShardSize** | DistributedTraining.lean | NodeAssignment.naturalLanguageShardSize | Burden | Shard size (load) |
| **codingLanguageShardSize** | DistributedTraining.lean | NodeAssignment.codingLanguageShardSize | Burden | Shard size (load) |
| **sizeMB** | DistributedTraining.lean | DatasetInfo.sizeMB | Burden | Dataset size (load) |
| **records** | DistributedTraining.lean | DatasetInfo.records | Burden | Record count (load) |
| **shards** | DistributedTraining.lean | DatasetInfo.shards | Burden | Shard count (load) |
| **shardSizeRecords** | DistributedTraining.lean | DatasetInfo.shardSizeRecords | Burden | Shard size (load) |
| **parallel** | DistributedTraining.lean | PipelinePhase.parallel | Adaptation | Parallel execution (pacing) |
| **faultTolerance** | DistributedTraining.lean | TrainingConfiguration.faultTolerance | Protection | Fault tolerance (protection) |
| **loadBalancing** | DistributedTraining.lean | TrainingConfiguration.loadBalancing | Burden | Load balancing (load) |
| **dataSharding** | DistributedTraining.lean | TrainingConfiguration.dataSharding | Adaptation | Data sharding (reorganization) |
| **networkUtilization** | DistributedTraining.lean | TrainingGuarantees.networkUtilization | Burden | Network utilization (load) |
| **resourceUtilization** | DistributedTraining.lean | TrainingGuarantees.resourceUtilization | Burden | Resource utilization (load) |
| **coordination** | DistributedTraining.lean | TrainingGuarantees.coordination | Adaptation | Coordination (pacing) |

## Collapsed Area Definitions

### Burden Area B
```
B = B(costEstimate, priority, lines, coverage, impactWeight, effortWeight, 
     cores, ramGB, storageGB, totalCores, totalRAMGB, totalNodes, gpuNodes,
     weight, coresAllocated, ramAllocatedGB, naturalLanguageShardSize,
     codingLanguageShardSize, sizeMB, records, shards, shardSizeRecords,
     networkUtilization, resourceUtilization, loadBalancing, ammr, avmr,
     inputSize, outputSize, bias, mutualInfo)
```

### Geometry Area G
```
G = G(kappaSquared, kappaHierarchy, geometricEfficiency, torsionalStress,
     interlockingEnergy, laplacianEnergy, grad_phi, laplacian_lb,
     w, x, y, z, weights, coupling, center, basinRadius, potential,
     metric, dimension, ricciCurvature, couplingStrength, couplingRadius,
     couplingDecay)
```

### Adaptation Area A
```
A = A(scaling_param, learning_rate, flowVel, isFixedPoint, isOptimized,
     dampingRate, expertiseLevel, hybridizationScore, parallel, dataSharding,
     coordination)
```

### Protection Area P
```
P = P(epsilonMutation, preservesInvariants, isIFSSet, threshold, isOptimized,
     dampingCoefficient, velocityThreshold, accelerationThreshold,
     hasTheorems, hasEvals, importGraphComplete, theoremCoverage,
     threshold, faultTolerance)
```

## PIST Operator

The unified PIST operator becomes:

```
q_{t+1} = PIST(q_t; B, G, A, P)
```

Where:
- B = Burden area (collapsed burden variables)
- G = Geometry area (collapsed geometry variables)
- A = Adaptation area (collapsed adaptation variables)
- P = Protection area (collapsed protection variables)

Each area can still unpack locally when needed for specific domain operations.

## Computational Load Assessment

**Lean compilation/proof burden:**
- Local reduction from removing stronger hypotheses
- Replacing hard proof obligations with `True := sorry`
- Simplifying theorem statements
- This is a proof-engineering reduction, not a runtime behavior claim

**Model architecture reduction:**
- 80 local rules → 1 primary update operator plus support quantities
- Collapsing dozens of local variables into 4 unified areas
- Replacing many domain-specific update rules with shared operator
- Reducing cross-domain translation overhead
- Reducing duplication in burden, geometry, adaptation, protection conceptualization

**Honest estimates:**
- Conceptual control load: 70-90% reduction
- Variable management burden: 80-95% reduction
- Actual total system complexity: reduced much less (complexity still present, just organized better)
- Cross-domain translation burden: largest win (primary pain point addressed)

**Key insight:**
The collapse did not remove the underlying complexity of the framework, but it significantly reduced its operational burden by shrinking the number of active control surfaces, translation paths, and duplicated update rules.

**Sharp version:**
Reduced orchestration cost more than raw complexity.
