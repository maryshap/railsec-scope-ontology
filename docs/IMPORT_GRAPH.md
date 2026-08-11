# Module import graph

**Decision ID:** IMPORT-B-001  
**Status:** fixed for the 0.1.0 line

```mermaid
flowchart LR
  V["Validation root (build-only)"] --> M4["M4 Assessment"]
  V --> M5["M5 Railway"]
  V --> RULES["Rule metadata"]
  M4 --> M3["M3 Results"]
  M3 --> M2["M2 Criteria"]
  M2 --> M1["M1 Core"]
  M5 --> M2
  M5 --> M1
  RULES --> M3
  M1 --> META["Suite metadata"]
  M2 --> META
  M3 --> META
  M4 --> META
  M1 --> PROV["PROV-O DL projection"]
```

M2 and M3 use PROV-O through the transitive M1 import, while their project-specific mappings are declared in their home modules. M6 case datasets contain individuals only; the validation orchestrator loads them with M5 and the validation root rather than making terminology modules import case data.

The graph is acyclic. `ontology/validation.ttl` is a build entry point, not a public terminology module, which avoids making the suite metadata import its own importers.
