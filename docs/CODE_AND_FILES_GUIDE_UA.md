# Путівник по коду та файлах

Це актуальна карта репозиторію після виконання implementation plan. Вона відділяє формально перевірений код від доменних тверджень, які ще потребують експертного погодження.

## Як запускати все

Основна команда — `scripts\validate.ps1`. Вона послідовно:

1. перевіряє повний import closure як OWL 2 DL;
2. запускає HermiT для consistency та class hierarchy;
3. окремо перевіряє ETCS case;
4. порівнює inferred hierarchy та 76-entity matrix із committed reports;
5. звіряє M1–M4 із frozen Gate B;
6. запускає module/publication lint;
7. виконує unit, SHACL, CQ та ETCS regression tests;
8. доводить, що навмисно суперечливий fixture відхиляється reasoner-ом.

Параметр `-UpdateHierarchy` можна використовувати лише після ручного перегляду очікуваної зміни hierarchy/matrix.

## Кореневі файли

- `README.md` — короткий вхід у проєкт і команда validation.
- `catalog-v001.xml` — локальне зіставлення ontology IRI з файлами; завдяки йому тести не залежать від мережі.
- `requirements.txt` — RDFLib, OWL-RL і pySHACL для Python-тестів.
- `tools/robot.jar` — pinned ROBOT 1.9.10 з OWLAPI та HermiT; checksum у `tools/README.md`.
- `.github/workflows/validate.yml` — той самий validation harness у CI.

## `ontology/`: TBox і RBox

- `ontology.ttl` — metadata suite, annotation properties, stable identifier і декларації зовнішніх annotation/datatype terms.
- `core.ttl` (M1) — Element/Asset/Interface/InformationFlow, Function, assertions, boundary, access, consequence; 27 frozen classes плюс явно схвалене Phase 2 розширення `Payload`.
- `criteria.ttl` (M2) — criteria, sources, interpretations, versioned artefacts, factors, coverage, deprecation; 19 classes.
- `results.ttl` (M3) — evaluations, assignments, Runs, derivation, reachability, ordering, coverage і performance; 26 classes. Тут знаходяться точні cardinality restrictions vertical slice.
- `assessment.ttl` (M4) — AssessorDecision, Inclusion, Exclusion, Override; 4 classes.
- `railway.ttl` (M5) — railway vocabulary: payload types, EN 50159 categories and threats, channel defences, traceable category-input assertions, SIL, access і fail-safe dependency. Safeguard→threat annotations є документацією, не reasoning axioms.
- `validation.ttl` — build-only root, який завантажує M4, M5 і rule metadata як один closure; не є публічним модулем.

OWL відповідає за open-world semantics, hierarchy, disjointness, domains/ranges і cardinality. Він не замінює SHACL closed-world validation.

## `imports/`

- `prov-o-source.ttl` — незмінена канонічна W3C копія для evidence.
- `prov-o-dl.ttl` — мінімальна перевірена OWL 2 DL projection лише використаних PROV-O terms.
- `README.md` — джерело, дата, checksum і пояснення, чому потрібна projection.

CR-B-006 документує це рішення: канонічний PROV-O документ використовує property punning, яке OWLAPI відхиляє з DL profile.

## `rules/`

- `classify-candidate.rq` — L2-R01: satisfied CriterionEvaluation для criterion, який визначає CandidateExaminationTarget, додає class membership елементу. Усі variables обмежені вже названими IRI, тому execution profile є DL-safe.
- `evaluate-transmission-category.rq` — створює три outcomes для кожного потоку (`satisfied`, `notSatisfied`, `undetermined`) і повний DerivationRecord із використаними facts/assumption.
- `classify-transmission-category.rq` — додає Category 1/2/3 membership лише для `satisfied` evaluation.
- `rules.ttl` — versioned metadata і Mechanism records правил, а не дубль executable text.

Rule створює semantic membership. `CategoryAssignment` лише матеріалізує membership і перевіряється K-23.

## `shapes/` і `queries/`

- `constraints.ttl` — локальні K-01–K-10, K-12–K-18, K-21.
- `criterion-slice.ttl` — CriterionEvaluation/CategoryAssignment, K-11 і regression для K-24.
- `railway.ttl` — M5 input/provenance shapes та перевірка, що category membership має satisfied evaluation.
- `boundary-assessment-coverage.rq` — рахує total/determined/undetermined; `undetermined` не випадає зі знаменника.
- `evaluation-stage-coverage.rq` — універсально рахує повноту будь-якої criterion stage з P/N/U outcomes, включно з candidate, для якого evaluations відсутні або undetermined.
- `K-23-assignment-agreement.rq` — знаходить assignment без відповідного entailment у тому самому Run.
- `K-24-layer-authority.rq` — знаходить забороненого L3/assessor producer.
- `queries/cq/CQ-09.rq` — повний regression query vertical slice; єдиний файл для CQ-09 після усунення дубліката.
- `queries/cq/CQ-01.rq` … `CQ-45.rq` — Gate A suite; усі parse і smoke-execute. Лише CQ-09 наразі має повний asserted answer oracle.

Structural SHACL запускається до OWL domain/range inference. Інакше неправильний owner властивості міг би автоматично отримати потрібний type і приховати defect.

## `fixtures/`, `profiles/`, `cases/`

- `fixtures/architecture/positive.ttl` — мінімальний conforming one-InstanceSet graph.
- `fixtures/k-constraints/negative-all.ttl` — навмисні дефекти, які доводять firing кожного local K-shape.
- `fixtures/criterion-slice/` — positive/negative end-to-end semantics.
- `fixtures/railway-category/` — мінімальний зростаючий стенд для Category 1/2/3 та undetermined, плюс invalid provenance case.
- `fixtures/boundary-coverage/` — regression, що undetermined boundary не завищує coverage.
- `fixtures/reasoner/inconsistent.ttl` — один individual як disjoint Asset та Interface.
- `profiles/RAILWAY_ARCHITECTURE_INSTANCE_PROFILE.md` — контракт M6 data і порядок stage processing.
- `cases/etcs/abox.ttl` — новий workbook-mapped ETCS ABox без legacy IRI.
- `cases/etcs/mapping.csv` — явні transformation rules.
- `cases/etcs/unmapped.csv` — поля, які не можна було чесно перенести.
- `cases/etcs/COMPARISON_WITH_LEGACY.md` — пояснення кожної категорії відмінностей.

## `migration/`

- `legacy-rule-triage.csv` — 54/54 legacy rules, кожне з рішенням `map` або `refactor`; усі мають `domain-review-required`.
- `write_legacy_rule_triage.py` — відтворює matrix із legacy generator.
- `extract_etcs_workbook.mjs` — read-only extraction workbook через artifact-tool.
- `migrate_etcs_case.py` — явна JSON→M6 mapping pipeline; не читає і не копіює legacy ABox.

Критична mapping межа: legacy `SecurityLevel` не є SIL, тому воно не мапиться на `SafetyIntegrityLevel`. DataObjects, Actors/Roles, security flags і AHP теж не губляться мовчки — вони записані як unmapped.

## `scripts/`, `tests/`, `reports/`

- `audit_formalisation.py` — точна звірка 76 frozen classes плюс governed conceptual changes; extension/revision admission policy не дозволяє використати каталог як обхід Gate B.
- `publication_lint.py` — K-19/K-20 та automated guard K-22.
- `write_inferred_hierarchy.py` — stable reasoner report.
- `write_entity_matrix.py` — 76-row traceability/formalisation inventory.
- `write_cq_suite.py` — deterministic generator 45 query files.
- `tests/` — CQ parsing/execution, K-shapes, publication lint, vertical slice й ETCS case.
- `reports/inferred-class-hierarchy.tsv` — committed reasoner output для semantic diff.
- `reports/entity-formalisation-matrix.tsv` — машинно згенерована карта всіх 76 entities.

## Що ще не можна називати завершеним

- Category rule працює на provisional JudgementBasis; production M5 criteria не release-ready без exact standard SourceLocation/Interpretation review.
- Основні Phase 2 rule blocks та orchestrator реалізовані. L3 вже виконує reachability, witness paths, candidate-set projection і coverage для явного Selection; weighted ordering очікує затвердженого методу.
- Для CQ-01–CQ-45 потрібна повна P/N/U fixture-oracle matrix; smoke execution недостатньо для наукової валідації.
- Workbook boundary mapping має бути підтверджений domain expert.
- K-22 вимагає ручного copyright/source-text review.
- Старий AHP навмисно не перенесений. Reachability/path/coverage реалізовані в новій архітектурі; factor computation і replacement ordering method ще мають бути затверджені.

Отже, зараз репозиторій має працюючу формальну основу, validation layers і structurally valid ETCS migration. Він навмисно не видає неперевірені legacy rules за доведену railway semantics.
