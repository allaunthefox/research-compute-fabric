the current window. The arrival window is the one immediately following the candidate transition, so the fusion rule is inherently predictive, not contemporaneous."

6. **No ground truth for prime gaps**:
   "There is no known 'true' critical transition in prime gaps. All detected events are unvalidated. The method can only flag candidate windows for further study, not confirm a phase change."

7. **Parameter sensitivity**:
   "Results depend on window size (n=8), step size (1), and feature thresholds. Small changes in n or thresholds can eliminate or create signals. Report sensitivity analysis."

8. **Edge effects**:
   "The first and last n-1 windows have incomplete neighbors for the fusion rule. Exclude them or treat separately."

9. **Reproducibility**:
   "All code, data, and random seeds must be published. The permutation null requires exact replication of the shuffling procedure."

10. **Interpretation caveat**:
    "Even if a window passes all criteria, it may be a false positive due to the heuristic thresholds and null mismatch. Do not claim statistical significance without a valid null model."