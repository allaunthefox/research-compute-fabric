---
project: GraphPlumbing
domain: axis-06-safety
type: MarkdownSpec
settlement: FORMING
authority: registry
route_signature: graph-plumbing/axis-06-safety/markdownspec/authority-matrix/v0
---

# Authority Matrix v0

| Surface | Role | May update canonical Lean? | May update FAMM? |
|---|---|---:|---:|
| Lean / Graph.lean | canonical structure and proof authority | yes | yes |
| GitHub | code/provenance surface | only through CI/proof gates | yes, if canonical/evidence routed |
| GraphML | graph transport | no | no |
| Mermaid | static projection | no | no |
| Ace Knowledge Graph | interactive projection | no | no |
| Notion | semantic registry/spec source | no | only after normalization |
| Linear | task/action graph | no | no by default |
| Airtable | operational mirror | no | no by default |
| Consensus | literature context | no | evidence only |
| Figma | diagram/presentation projection | no | no |

## Rule

Projection and mirror surfaces cannot mutate canonical graph or FAMM basins directly.
