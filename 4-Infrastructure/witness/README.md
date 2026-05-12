# Witness Sources

`sources.json` is the provider registry for artifact lifecycle reports. It is
deliberately source-agnostic: GitHub, GitLab, Forgejo, bare git, Mercurial, CVS,
science-toolbelt probes, DeepSeek receipts, and SHA-256 ledgers are all source
blocks with a backend descriptor.

Operating rule:

> Observation changes the receipt surface, not the underlying law.

Sources emit reports. They do not make mathematical claims true. Lean modules,
claim-registry promotion, and receipt validators decide what can be treated as
formal or review evidence.

## Source Blocks

Each source block should identify:

- `active`: whether the stack should listen to it now.
- `backend`: `{type, kind, host}` or the closest equivalent.
- `url`: file path, repository URL, artifact directory, or logical endpoint.
- `hook_kind`: how events are observed, such as `webhook`, `server-side`,
  `filesystem`, or `post-event-script`.
- `schema`: optional machine-readable receipt schema.
- `cost_policy`: optional bind-cost hints for source-event adapters.

Unknown future backends should be added as new source blocks first. Code should
only grow an adapter once a source produces real receipts worth consuming.

## Current Consumers

- `0-Core-Formalism/lean/Semantics/Semantics/ProvenanceSource.lean` defines the
  open formal shape of source events.
- `5-Applications/tools-scripts/substrate/substrate_git_index.py` uses the
  source registry when installing git post-receive hooks.
- `5-Applications/scripts/attest_signal_wave_unification.py` stores
  provider-tagged attestation records.
