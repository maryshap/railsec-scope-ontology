# Payload direction — unresolved

## What's missing

1 safety-related payload classification remains unattached — down from 5.
The other 2 (`payload-DO-21` on `IF-TS-03` and `IF-TS-06`) were resolved
directly: both interfaces have exactly one flow traversing them, so there
was no direction to choose — attaching the payload to that sole flow is a
correction, not a guess, and has been applied to
`cases/etcs/security-facts.ttl` already.

The source/data review resolved two additional mappings from the workbook's
producer/consumer columns and the directed interface endpoints:

- `payload-DO-04` is carried by `flow-if-rad-03-reverse` (RBC to EVC).
- `payload-DO-05` is carried by `flow-if-rad-01-forward`, the outbound
  EVC/CAB-Radio path segment toward the radio access network.

Each mapping has an `AssertedFact` and exact worksheet-row `SourceLocation` in
`classification-provenance.ttl`. The remaining record is not merely ambiguous;
its source fields conflict at the interface boundary:

| Payload | Was attached to (interface, wrong) | Candidate flows (need a direction decision) |
|---|---|---|
| `payload-DO-04` | `interface-if-ct-01` | workbook says RBC produces DO-04 for EVC, but IF-CT-01 connects RBC and IXL; neither direction establishes delivery to EVC |

## Why this isn't fixed alongside the protection-property fix

The 616 protection-control facts (`authenticationEnabled` etc.) were fanned
out to every flow traversing the affected interface, because a protection
mechanism genuinely applies to the physical/logical channel in both
directions — this mirrors the precedent already set in
`cases/etcs/transmission-environment.ttl` (CR-B-022: medium and exposure
facts are attached to both directions of a flow for the same reason).

Payload content is directional. The two resolved links follow explicit
producer/consumer and endpoint data. Attaching DO-04 to either IF-CT-01 flow
would instead conceal a source inconsistency, so it remains unresolved.

## What would resolve this properly

A source that states the direction explicitly:

- A controlled interface/message specification linking the Movement Authority
  to the RBC–IXL segment could resolve the remaining IF-CT-01 record.
- Published ETCS/ERTMS specification material (e.g. SUBSET-026) describing
  what `DO-04`, `DO-05`, `DO-21` actually are, if their real-world meaning
  can be established, would settle the direction independent of this
  dataset.
- If no source settles it, the honest option is to leave it unresolved and
  let dependent evaluations stay `undetermined` for that mapping — that is
  what the rules already do by design when a
  determination isn't available, and it is a legitimate result, not a gap
  to paper over.

## What NOT to do

Do not attach `carriesPayload` to whichever flow direction makes the
demo/scenario more interesting. Direction picked for narrative convenience
would be indistinguishable, later, from direction picked for a real
reason — and the whole point of this project's provenance discipline is
that it never becomes indistinguishable.
