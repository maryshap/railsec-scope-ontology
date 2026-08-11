# Pinned validation tool

`robot.jar` is ROBOT 1.9.10 from the official ontodev/robot GitHub release.

- Source: `https://github.com/ontodev/robot/releases/download/v1.9.10/robot.jar`
- SHA-256: `16A73C074F3DF359A7338A84B4E0788785FE06117F931BB9796E9619EA776105`
- Purpose: OWLAPI OWL 2 DL profile validation and HermiT classification/consistency checks.

The JAR is intentionally excluded from Git. CI downloads this exact release and refuses to run when its SHA-256 differs. Local validation uses `tools/robot.jar` after the same one-time download.
