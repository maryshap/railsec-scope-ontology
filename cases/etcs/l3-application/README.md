# Applying the completed L3 profile to ETCS

The L3 mechanism is complete for its declared minimal ATT&CK ICS 19.2 profile.
This directory concerns case-data readiness and retained ETCS results, not a
new ontology layer.

## Preconditions for a material ETCS attack path

1. A railway zone has a reviewed semantic type such as `ExternalZone` or
   `DMZZone`.
2. An asset in that zone receives a satisfied entry-point criterion evaluation.
3. The entry asset has an explicitly evidenced `reachableBy` access mechanism.
4. Directed outgoing flows are evaluated by L1-L2 criteria.
5. Every path step has a satisfied technique-applicability evaluation and its
   satisfied prerequisite evidence in the same Run.
6. Safety links and payload direction are used only where stated in the case
   evidence.

## Current readiness

- Flow-level applicability: computable for criteria whose L1-L2 inputs exist.
- Asset entry-point applicability: zone semantics are now available for Z-06
  (`ExternalZone`) and Z-IT-FW (`DMZZone`); applicability may be evaluated for
  assets whose remaining criterion inputs exist.
- Attack-path materialisation: blocked pending entry access evidence, even if
  entry-point classification is later supplied.
- Safety-critical target/function linkage: partially available.
- Fail-safe linkage: unresolved because `failSafeDependsOn` is absent.
- Safety-related payload linkage: available for four resolved directed flows;
  one conflicting DO-04/IF-CT-01 source mapping remains unresolved.

An empty result before these inputs are supplied is not evidence that no path
exists. ETCS L3 output becomes a material case-study result only after the
relevant preconditions are sourced or explicitly introduced as scenario
assumptions.
