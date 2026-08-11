# Pinned ontology imports

| File | Canonical source | Retrieved | SHA-256 |
|---|---|---|---|
| `prov-o-source.ttl` | `https://www.w3.org/ns/prov-o.ttl` | 2026-08-11 | `7D203989F67B38BCA572253942ACC5A1BF24CE3CCFECE16F072DCB4BE2B79A96` |
| `prov-o-dl.ttl` | reviewed projection of the pinned source | 2026-08-11 | verified by the validation harness |

`prov-o-source.ttl` is the unmodified official W3C Turtle encoding of PROV-O. The canonical document is not OWL 2 DL under OWLAPI because it uses `prov:specializationOf` and `prov:wasRevisionOf` as both annotation and object properties. The XML catalogue therefore resolves `http://www.w3.org/ns/prov-o` to `prov-o-dl.ttl`, a minimal OWL 2 DL-safe projection of the exact classes and properties used by this project. The harness validates the projection and full project import closure. Refreshing either file is a reviewed dependency change.
