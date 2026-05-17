# Kernel Boundary SVM/QML Prior

Status: `EXTERNAL_REFERENCE_WITH_CANDIDATE_STACK_MAPPING`

Sources:

- scikit-learn SVM user guide: `https://scikit-learn.org/stable/modules/svm.html`
- Quantum Machine Learning overview: `https://thequantuminsider.com/2026/05/08/what-is-quantum-machine-learning/`

## Why This Matters

Support Vector Machines give the stack a clean boundary primitive:

```text
feature field -> margin boundary -> support-vector witnesses -> replayable decision
```

The useful part is not generic classification. The useful part is that the
decision boundary depends on a sparse subset of training points: the support
vectors. In Research Stack terms, those support vectors are candidate receipt
leaves for the boundary.

This maps naturally to SMN/eigenmass work:

```text
all observed rows/cells
  -> kernel feature space
  -> support-vector boundary witnesses
  -> Mass Number / SMN gate context
  -> ADMIT, HOLD, or QUARANTINE
```

## Classical Kernel Surface

SVMs support classification, regression, and outlier/novelty detection. Their
strength is high-dimensional boundary finding, especially when the number of
dimensions is large. Their risk is overfitting and compute blow-up when kernel
choice, regularization, and sample size are not controlled.

For stack use:

| SVM term | Stack mapping |
|---|---|
| Support vector | Boundary witness leaf |
| Margin | Admissibility buffer |
| Kernel | Feature-space projection law |
| Decision function | Route/gate score |
| `sample_weight` / `class_weight` | SMN/evidence-load weighting |
| One-class SVM | Outlier / quarantine detector |

## Quantum Kernel Surface

The QML article is useful because it describes the same kernel pattern with a
different feature-map backend:

```text
classical data
  -> quantum feature map / circuit encoding
  -> sampled quasi-probabilities
  -> kernel matrix
  -> classical SVM decision
```

That makes quantum kernels a possible future `kernel backend`, not a new claim
class. The stack can keep the same receipt requirements:

```text
kernel backend declared
support witnesses emitted
kernel matrix hash recorded
decision function replayed
negative controls pass
```

## Claim Boundary

Allowed:

- Use classical SVMs as a baseline boundary detector.
- Treat support vectors as sparse boundary receipts.
- Use one-class SVM as a quarantine/outlier prior.
- Treat quantum kernels as an optional future backend for kernel-matrix
  generation.

HOLD:

- Quantum advantage.
- Commercially relevant QSVM superiority.
- Any hardware quantum claim.
- Any physical mass claim from semantic support vectors.
- Any proof claim without Lean/replay receipts.

## First Fixture

Recommended first fixture:

```text
input: DESI/MaNGA joined-cell eigenmass features
label: avalanche-candidate vs non-candidate, or HOLD/ADMIT proxy
baseline: linear SVM and RBF SVM
receipt: support indices, support-vector hash, kernel params, decision scores,
         train/test split hash, shuffled-label negative control
decision: ADMIT_FIXTURE or HOLD
```

The kernel must be treated as a projection law, not as authority. The support
vectors are useful only if the replay receipt closes.
