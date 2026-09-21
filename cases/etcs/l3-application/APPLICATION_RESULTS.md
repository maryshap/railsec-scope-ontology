# ETCS L3 application results

## Evidence boundary

GitHub Actions run `35572456116` completed successfully for commit
`9038d03211ed84f02a5abdbf410cf5263ade5f2a`. It produced the case-data audit
and all six scenario evidence artefacts. The artefact metadata identifies the
same commit and all seven artefacts are retained until 2026-10-21.

The counts below were reproduced with
`scripts/summarise_etcs_l3_application.py` by applying that commit's
deterministic L3 computation in memory to the locally retained publishable
scenario graphs from run `34902020626`. This was necessary because GitHub
permits unauthenticated reading of public artefact metadata but requires an
authenticated session to download the ZIP payloads. No case fact was added or
defaulted during this reproduction.

## Scenario comparison

Every scenario evaluates the complete declared profile over 148 directed flows
and 92 assets: 1,812 technique-applicability evaluations per Run.

| Scenario | Satisfied | Not satisfied | Undetermined | Distinct satisfied techniques | Attack paths |
|---|---:|---:|---:|---:|---:|
| protected-baseline | 16 | 1,796 | 0 | 1 | 0 |
| missing-safety-code | 16 | 1,796 | 0 | 1 | 0 |
| missing-corruption-protection | 17 | 1,795 | 0 | 2 | 0 |
| unknown-data | 16 | 1,796 | 0 | 1 | 0 |
| combined-degradation | 17 | 1,791 | 4 | 2 | 0 |
| realistic-legacy | 218 | 466 | 1,128 | 4 | 0 |

The 16 satisfied evaluations common to every scenario are T0886 Remote
Services applicability records for the sourced ExternalZone/DMZZone entry
assets. They establish technique applicability, not successful access.

## Interpretation

- The protected baseline has no satisfied flow-level technique applicability.
- Removing only the safety code changes no L3 result because the explicit
  cryptographic alternative prevents the upstream corruption threat; this is
  the preregistered L2 behaviour, not a missing L3 inference.
- Removing both corruption-protection alternatives produces one satisfied
  T0830 Adversary-in-the-Middle applicability evaluation on the affected flow.
- The combined scenario retains that T0830 result and four undetermined
  sequence-related applicability evaluations rather than coercing missing
  evidence to false.
- The realistic legacy data produces satisfied applicability for T0814 Denial
  of Service (16), T0830 Adversary-in-the-Middle (59), T0842 Network Sniffing
  (127), and T0886 Remote Services (16). Large undetermined counts remain
  visible where L1-L2 prerequisites are incomplete.
- The unknown-data scenario changes an upstream threat-deletion result to
  undetermined as preregistered, but does not change an L3 prerequisite in the
  current minimal profile; therefore its L3 aggregate remains equal to the
  protected baseline.

## Why there are no material attack paths

All scenarios contain 16 derived EntryPoint assets but zero explicit
`reachableBy` facts. The attack-aware traversal therefore has no evidenced
access mechanism from which to start. Zero materialised paths means
"insufficient access evidence", not "no attack path exists".

The next ETCS input must be one of the following, kept explicit and sourced:

1. deployment or expert evidence stating which entry assets are reachable by
   which remote, local, physical or maintenance access mechanisms; or
2. a separately named controlled attack scenario whose `reachableBy` facts are
   clearly marked as attributed assumptions rather than deployment facts.

Until one of those evidence sets exists, creating an ETCS `AttackPathResult`
would violate the L3 provenance contract.

After this six-scenario result set was recorded, option 2 was implemented as
the separately pre-registered `controlled-remote-attack-path` scenario. It is
not included in the table above. Its result belongs in this report only after
the full GitHub reasoner/SHACL workflow and the dedicated path verifier pass.
