# Prime Gap Entropy-Collapse Rerun Receipt — K=21

Date: 2026-05-11

Purpose: rerun the prime-gap entropy-collapse detector with the corrected
selective braid threshold from
`6-Documentation/docs/distilled/ArithmeticSpec_Corrected_2026-05-11.md`.

Method:

- Generate the first N primes by sieve.
- Convert to prime gaps.
- Use sliding adjacent windows of width W=8.
- Braid component compares `gaps[t:t+8]` to arrival window `gaps[t+1:t+9]`
  with dense-rank Kendall crossing count and tied pairs excluded.
- `sigma_q` and `D2` are evaluated on the arrival window.
- Thresholds:
  - old braid: `crossing_count > 7`
  - corrected strict braid: `crossing_count > 21`
  - inclusive convention check: `crossing_count >= 21`
  - `sigma_q < 0.4`
  - `D2 < 0.7`

Results:

| Prime prefix | Windows | sigma_q and D2 collapsed | Old triple `cross>7` | Inclusive triple `cross>=21` | Strict triple `cross>21` |
|---:|---:|---:|---:|---:|---:|
| 10,000 | 9,991 | 2,324 | 2,084 | 1 | 0 |
| 100,000 | 99,991 | 14,486 | 12,932 | 28 | 3 |
| 1,000,000 | 999,991 | 96,213 | 86,565 | 190 | 38 |

Braid-tail-only counts:

| Prime prefix | `cross>7` | `cross>=21` | `cross>21` |
|---:|---:|---:|---:|
| 10,000 | 9,493 | 175 | 69 |
| 100,000 | 95,399 | 2,520 | 1,097 |
| 1,000,000 | 961,680 | 29,727 | 13,458 |

First strict `cross>21` fires in the first 1,000,000-prime run:

| t | crossing_count | sigma_q | D2 | A window | arrival B window |
|---:|---:|---:|---:|---|---|
| 51541 | 22 | -0.2074438511 | 0.6666666667 | `[8, 6, 16, 14, 4, 26, 4, 26]` | `[6, 16, 14, 4, 26, 4, 26, 4]` |
| 71717 | 23 | -0.3531147388 | 0.6666666667 | `[10, 6, 8, 18, 4, 26, 4, 26]` | `[6, 8, 18, 4, 26, 4, 26, 4]` |
| 88616 | 22 | -1.0248839184 | 0.6666666667 | `[4, 24, 8, 22, 8, 22, 12, 18]` | `[24, 8, 22, 8, 22, 12, 18, 8]` |
| 117020 | 22 | -0.1492588333 | 0.5593573017 | `[2, 18, 6, 10, 8, 10, 8, 10]` | `[18, 6, 10, 8, 10, 8, 10, 8]` |
| 136640 | 23 | -0.5517217501 | 0.6666666667 | `[24, 12, 14, 30, 4, 32, 4, 32]` | `[12, 14, 30, 4, 32, 4, 32, 4]` |

Conclusion:

The original prime-gap result was mostly an artifact of the non-selective
`K=7` braid threshold. With the corrected strict threshold `crossing_count > 21`,
the detector still fires, but only rarely: 38 strict fires across 999,991
windows in the first 1,000,000 primes. Under the inclusive `crossing_count >= 21`
convention, it fires 190 times across the same run.

Interpretation:

- The prime-gap "signal" does not disappear completely.
- It does not support the earlier broad claim that the detector fires commonly
  on prime gaps without calibration.
- The surviving strict fires are rare structured windows dominated by repeated
  alternating small/large gap motifs and should be treated as candidates for
  follow-up characterization, not as a general prime-gap phenomenon.
