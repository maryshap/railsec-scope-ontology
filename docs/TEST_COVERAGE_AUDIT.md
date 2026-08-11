# Test coverage audit

The executable files alone do not establish semantic coverage. This audit records where a green result is backed by an answer oracle or exercised SHACL focus nodes, and where it is only a tracked implementation gap.

## Competency questions

- 9/45 CQs return an asserted number of rows on the representative graph.
- 4/45 are required to be empty by design.
- 32/45 are pending capabilities and are asserted empty as a ratchet.

Every CQ belongs to exactly one class. A pending CQ that starts returning data fails until it is deliberately promoted and given an answer oracle.

## SHACL shapes

- 4/21 node shapes currently have focus nodes in the evaluated case/architecture data.
- 17/21 are implemented and have negative fixtures, but remain vacuous on the positive data because their producing capability is pending.

Every node shape is registered as exercised or unexercised. New unregistered shapes and accidental loss of focus-node coverage fail the suite.

## Decision

The registries are accepted as visibility guards, not as substitutes for implementation. Their counts must improve as rule blocks, the orchestrator, L3 results and study-case evidence are added.
