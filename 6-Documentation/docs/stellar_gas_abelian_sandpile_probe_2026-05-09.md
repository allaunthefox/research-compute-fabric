# Stellar Gas Abelian Sandpile Probe

Status: `SANDPILE_DIAGNOSTIC`

Decision: `ADMIT_SANDPILE_DIAGNOSTIC_HOLD_PHYSICAL_SANDPILE`

This probe treats the stellar-gas eigenmass surface as an Abelian-sandpile-style
diagnostic. Cells carry normalized eigenmass as "grains"; gas/shock observables
act as toppling pressure; high grain/high-pressure cells become avalanche
candidates for fine-grained follow-up.

Claim boundary: this is a metaphor-backed diagnostic over observational proxies.
It is not a physical sandpile simulation, not stellar mass, not direct gas
density inference, and not a cosmology fit.

## Channel Correlations With Eigenmass

- `log_desi_count`: 0.881673842
- `stellar_sigma_mean`: 0.878922036
- `partial_full_shock_fraction`: 0.847109384
- `shock_score_mean`: 0.839508306
- `shock_lier_fraction`: 0.811272006
- `star_forming_fraction`: -0.718656679
- `agn_liner_or_shock_fraction`: 0.708425115
- `gas_sigma_mean`: 0.654818267
- `gas_sigma_p90`: 0.605869064
- `snr_mean`: -0.435451409
- `log_manga_count`: 0.097331989

## Toppling Candidates

- `ra03_north__z_008_plus`: state `AVALANCHE_CANDIDATE`, grains `0.11642`, pressure `1.157125106`, index `1.596155368`
- `ra03_south__z_008_plus`: state `AVALANCHE_CANDIDATE`, grains `0.112959`, pressure `1.198262192`, index `1.570637955`
- `ra04_north__z_008_plus`: state `AVALANCHE_CANDIDATE`, grains `0.11274`, pressure `1.17842835`, index `1.557804876`
- `ra02_south__z_008_plus`: state `AVALANCHE_CANDIDATE`, grains `0.107057`, pressure `1.208401092`, index `1.497117602`
- `ra02_north__z_008_plus`: state `AVALANCHE_CANDIDATE`, grains `0.110828`, pressure `1.09454727`, index `1.490404542`
- `ra02_south__z_006_008`: state `LOADED`, grains `0.047288`, pressure `1.540624514`, index `0.867357748`
- `ra03_north__z_006_008`: state `LOADED`, grains `0.039897`, pressure `0.645551377`, index `0.321404162`
- `ra02_north__z_006_008`: state `LOADED`, grains `0.03392`, pressure `0.577987139`, index `0.208033555`
- `ra04_north__z_006_008`: state `LOADED`, grains `0.034318`, pressure `0.362305657`, index `0.105492499`
- `ra03_south__z_006_008`: state `STABLE`, grains `0.024638`, pressure `0.337625686`, index `-0.035744352`

## Pressure Components

```json
[
  "partial_full_shock_fraction",
  "shock_lier_fraction",
  "shock_score_mean",
  "gas_sigma_mean",
  "gas_sigma_p90",
  "agn_liner_or_shock_fraction"
]
```

## Holds

- `HOLD_PHYSICAL_SANDPILE_SIMULATION`
- `HOLD_DIRECT_STELLAR_MASS`
- `HOLD_DIRECT_GAS_DENSITY_INFERENCE`
- `HOLD_OBJECT_LEVEL_CROSSMATCH`
- `HOLD_COSMOLOGY_FIT`

## Receipt Backlinks

- Receipt: `shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe_receipt.json`
- Source cell eigenmass receipt: `shared-data/data/stellar_gas_observation/stellar_gas_eigenvector_mass_probe_receipt.json`
- Data: `shared-data/data/stellar_gas_observation/stellar_gas_abelian_sandpile_probe.json`
- Tiddler: `6-Documentation/tiddlywiki-local/wiki/tiddlers/Stellar Gas Abelian Sandpile Probe.tid`
