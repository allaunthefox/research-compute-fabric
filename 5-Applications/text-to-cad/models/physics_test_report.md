# Merkle Jack Physics Test Report

Generated: 2026-04-28 04:50:04.011262

## Geometry Parameters

- Depth: 4
- Branching Factor: 2
- Branch Angles: [30.0, 25.0, 20.0, 15.0]
- Azimuthal Offsets: [0.0, 45.0, 90.0, 135.0]
- Tubule Radius: 1.5 mm
- Height per Level: 6.0 mm
- Total Nodes: 31
- Total Edges: 30

## Material Properties

- Young's Modulus: 200.0 GPa
- Shear Modulus: 79.3 GPa
- Yield Strength: 250.0 MPa
- Ultimate Strength: 400.0 MPa

## Test Results

### Compression - Moderate

**Description:** Compressive load equal to structure weight

**Load Type:** compression
**Magnitude:** 1000.0 N

**Maximum Stress:** 0.00 MPa
**Minimum Stress:** 0.00 MPa
**Mean Stress:** 0.00 MPa
**Standard Deviation:** 0.00 MPa
**Safety Factor:** inf
**Failure Edges:** 0/30

✅ **STRUCTURE SAFE**

### Compression - Heavy

**Description:** Heavy compressive load (10x structure weight)

**Load Type:** compression
**Magnitude:** 10000.0 N

**Maximum Stress:** 0.00 MPa
**Minimum Stress:** 0.00 MPa
**Mean Stress:** 0.00 MPa
**Standard Deviation:** 0.00 MPa
**Safety Factor:** inf
**Failure Edges:** 0/30

✅ **STRUCTURE SAFE**

### Tension - Uplift

**Description:** Upward tensile load at root

**Load Type:** tension
**Magnitude:** 5000.0 N

**Maximum Stress:** 353.68 MPa
**Minimum Stress:** 0.00 MPa
**Mean Stress:** 23.58 MPa
**Standard Deviation:** 88.22 MPa
**Safety Factor:** 0.71
**Failure Edges:** 2/30

⚠️ **FAILURE DETECTED** at edges: [(0, 1), (0, 2)]

### Shear - Lateral

**Description:** Lateral shear load in X direction

**Load Type:** shear
**Magnitude:** 2000.0 N

**Maximum Stress:** 9.43 MPa
**Minimum Stress:** 4.72 MPa
**Mean Stress:** 7.82 MPa
**Standard Deviation:** 1.24 MPa
**Safety Factor:** 26.51
**Failure Edges:** 0/30

✅ **STRUCTURE SAFE**

### Shear - Wind

**Description:** Wind load simulation (lateral shear)

**Load Type:** shear
**Magnitude:** 3000.0 N

**Maximum Stress:** 14.15 MPa
**Minimum Stress:** 9.31 MPa
**Mean Stress:** 10.91 MPa
**Standard Deviation:** 1.32 MPa
**Safety Factor:** 17.67
**Failure Edges:** 0/30

✅ **STRUCTURE SAFE**

### Torsion - Twist

**Description:** Torsional load about vertical axis

**Load Type:** torsion
**Magnitude:** 500.0 N

**Maximum Stress:** 408700.63 MPa
**Minimum Stress:** 77619.21 MPa
**Mean Stress:** 255747.17 MPa
**Standard Deviation:** 110916.35 MPa
**Safety Factor:** 0.00
**Failure Edges:** 30/30

⚠️ **FAILURE DETECTED** at edges: [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5)]

## Summary

- Safe Tests: 4/6
- Low Margin Tests: 0/6
- Failure Tests: 2/6

⚠️ **CRITICAL:** Structure fails under some load conditions.

