# Equation Forest Topology Map

**Last Updated:** 2026-04-28
**Total Nodes:** 14
**Total Connections:** 10
**Total Paths:** 6

## Forest Structure

### Domain Clusters

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE LOAD DOMAIN                        │
│  ┌──────────────┐    variableShared (100)    ┌──────────────┐ │
│  │intrinsicLoad │─────────────────────────────►│totalCognitive│ │
│  └──────────────┘                              │    Load     │ │
│                                                 └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FRAMEWORK/BRIDGE DOMAIN                      │
│  ┌──────────────┐    leanBridge (500)       ┌──────────────┐ │
│  │couchEquation │─────────────────────────────►│frameEvolution│ │
│  └──────────────┘                             │  Continuous  │ │
│                                              └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    THERMODYNAMICS DOMAIN                        │
│  ┌──────────────┐    familyConnection (300) ┌──────────────┐ │
│  │pressurePiling│─────────────────────────────►│hugoniotTemp  │ │
│  └──────────────┘                             │  erature    │ │
│                                              └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ELECTROCHEMISTRY DOMAIN (MOF)                │
│  ┌──────────────┐    electrochemical (150) ┌──────────────┐ │
│  │mofCO2_2e_    │─────────────────────────────►│mofCO2_2e_    │ │
│  │HCOOH         │                             │CO            │ │
│  └──────────────┘                             └──────────────┘ │
│         │                                            │          │
│         │                                            │          │
│         │    electronTransfer (400)                  │          │
│         └────────────────────────────────────────────┘          │
│                                                      │          │
│                                                      ▼          │
│                                              ┌──────────────┐ │
│                                              │mofCO2_6e_    │ │
│                                              │CH3OH         │ │
│                                              └──────────────┘ │
│                                                      │          │
│                                                      │          │
│                                    electronTransfer (200)│          │
│                                                      ▼          │
│                                              ┌──────────────┐ │
│                                              │mofCO2_8e_    │ │
│                                              │CH4           │ │
│                                              └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    TIME SERIES DOMAIN (AFFINE)                   │
│  ┌──────────────┐    timeSeries (250)        ┌──────────────┐ │
│  │affineLinear  │─────────────────────────────►│affineDecomp  │ │
│  │Layer         │                             │osition       │ │
│  └──────────────┘                             └──────────────┘ │
│                                                      │          │
│                                                      │          │
│                                    timeSeries (300)  │          │
│                                                      ▼          │
│                                              ┌──────────────┐ │
│                                              │affinePeriodic│ │
│                                              └──────────────┘ │
│                                                      │          │
│                                                      │          │
│                                    timeSeries (200)  │          │
│                                                      ▼          │
│                                              ┌──────────────┐ │
│                                              │affineScaled   │ │
│                                              │Periodic      │ │
│                                              └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Connection Type Distribution

| Connection Type | Count | Gradient Range | Usage |
|----------------|-------|----------------|-------|
| variableShared | 1 | 100 | Cognitive load relationships |
| familyConnection | 1 | 300 | Thermodynamic families |
| leanBridge | 1 | 500 | Framework bridging |
| electrochemical | 1 | 150 | MOF reaction pathways |
| electronTransfer | 2 | 200-400 | MOF electron transfer chains |
| timeSeries | 3 | 200-300 | Affine time series decomposition |

## Gradient Path Summary

| Path ID | Domain | Connections | Cost | Description |
|---------|--------|-------------|------|-------------|
| 0 | Framework + Cognitive | couchToFrame + loadToCognitive | 600 | Bridge to frame evolution |
| 1 | Thermodynamics | pressureToHugoniot | 300 | Pressure to temperature |
| 2 | MOF Electrochemical | mof2eCO_to_6eCH3OH + mof6eCH3OH_to_8eCH4 | 600 | CO → CH3OH → CH4 chain |
| 3 | MOF Electrochemical | mof2eHCOOH_to_2eCO | 150 | HCOOH → CO conversion |
| 4 | Affine Time Series | affineLinear_to_decomposition + affineDecomposition_to_periodic | 550 | Linear → Decomposition → Periodic |
| 5 | Affine Time Series | affinePeriodic_to_scaled | 200 | Periodic → Scaled Periodic |

## Domain Isolation Analysis

**Highly Connected Domains:**
- MOF Electrochemistry: 3 connections, 2 paths (internal chain structure)
- Affine Time Series: 3 connections, 2 paths (linear decomposition chain)

**Sparse Domains:**
- Cognitive Load: 1 connection, 1 path (isolated pair)
- Framework/Bridge: 1 connection, 1 path (isolated pair)
- Thermodynamics: 1 connection, 1 path (isolated pair)

**Cross-Domain Connections:** None currently - domains are isolated

## Forest Shape Characteristics

1. **Clustered Structure:** Forest consists of 5 isolated domain clusters
2. **No Cross-Domain Bridges:** No connections between different domains
3. **Linear Chains:** MOF and Affine domains form linear chains
4. **Gradient Distribution:** Costs range from 100-600 milli-units
5. **Path Length:** Paths range from 1-2 connections

## Potential Expansion Opportunities

1. **Cross-Domain Bridges:** Could connect thermodynamics to electrochemistry (temperature effects on reaction rates)
2. **Cognitive-MOF Integration:** Load monitoring for catalyst performance
3. **Framework-Affine Bridge:** Couch equation to time series forecasting
4. **Unified Gradient Surface:** Currently fragmented - could be unified with cross-domain connections
