# Payload direction — unresolved

## What's missing

3 safety-related payload classifications remain unattached — down from 5.
The other 2 (`payload-DO-21` on `IF-TS-03` and `IF-TS-06`) were resolved
directly: both interfaces have exactly one flow traversing them, so there
was no direction to choose — attaching the payload to that sole flow is a
correction, not a guess, and has been applied to
`cases/etcs/security-facts.ttl` already.

The 3 that remain genuinely ambiguous, because their interface has two
flows and the legacy model doesn't record which one carries the payload:

| Payload | Was attached to (interface, wrong) | Candidate flows (need a direction decision) |
|---|---|---|
| `payload-DO-04` | `interface-if-ct-01` | `flow-if-ct-01-forward`, `flow-if-ct-01-reverse` |
| `payload-DO-04` | `interface-if-rad-03` | `flow-if-rad-03-forward`, `flow-if-rad-03-reverse` |
| `payload-DO-05` | `interface-if-rad-01` | `flow-if-rad-01-forward`, `flow-if-rad-01-reverse` |

## Why this isn't fixed alongside the protection-property fix

The 616 protection-control facts (`authenticationEnabled` etc.) were fanned
out to every flow traversing the affected interface, because a protection
mechanism genuinely applies to the physical/logical channel in both
directions — this mirrors the precedent already set in
`cases/etcs/transmission-environment.ttl` (CR-B-022: medium and exposure
facts are attached to both directions of a flow for the same reason).

Payload content is different: it is directional. `DO-04` almost certainly
travels one way across `IF-CT-01`/`IF-RAD-03` (plausibly RBC→onboard,
consistent with a Movement Authority-shaped message, going by the labels),
not both. Attaching it to both `forward` and `reverse` would assert that the
acknowledgement/status traffic in the other direction also carries that
same safety-related content, which is not something the legacy model
records and not something derivable from the interface-level fact alone.
That would be inventing a determination, not transferring one — exactly
what `migrate_legacy_security_facts.py` documents itself as never doing.

## What would resolve this properly

A source that states the direction explicitly:

- The architecture documentation already in the project (general
  architecture / cartography PDFs) may show message direction for these
  specific interfaces.
- Published ETCS/ERTMS specification material (e.g. SUBSET-026) describing
  what `DO-04`, `DO-05`, `DO-21` actually are, if their real-world meaning
  can be established, would settle the direction independent of this
  dataset.
- If no source settles it, the honest option is to leave it unresolved and
  let critical-violation/fail-safe/SIL stay `undetermined` for these five
  payloads — that is what the rules already do by design when a
  determination isn't available, and it is a legitimate result, not a gap
  to paper over.

## What NOT to do

Do not attach `carriesPayload` to whichever flow direction makes the
demo/scenario more interesting. Direction picked for narrative convenience
would be indistinguishable, later, from direction picked for a real
reason — and the whole point of this project's provenance discipline is
that it never becomes indistinguishable.
