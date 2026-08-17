# Коротко: стара онтологія проти нової

## Основна різниця

Стара онтологія була **працюючим ETCS-oriented pipeline**, але її schema, rules, generated result classes, ABox і computations були тісно з'єднані.

Нова онтологія будується як **модульна railway-wide semantic framework**, у якій ETCS є окремим case study. Вона чітко розділяє terminology, case data, logical classification, external computations, integrity validation, provenance та human decisions.

| Стара | Нова |
|---|---|
| Загальний ICS/railway TBox змішаний із SIL, EN 50159, threats та ATT&CK | M1–M4 subsystem-independent; railway concepts підуть у M5; ETCS individuals — тільки в case ABox |
| Один великий ETCS ABox генерується з Excel | Кожна архітектура буде окремим versioned ABox за спільним railway instance profile |
| 54 custom rules; частина result classes створюється динамічно | Усі assessment concepts визначаються наперед; rules створюють evaluation/entailment із provenance |
| Custom RDFLib forward chaining називається SWRL-подібним reasoning | OWL, DL-safe rules, SHACL і L3 computations мають різних чітких власників |
| Висновок часто існує лише як class assertion | Розділені entailment, `CriterionEvaluation`, `CategoryAssignment`, `DerivedResult` і derivation record |
| Validation переважно перевіряє посилання Excel/ABox | Працюють OWL consistency, SHACL K-01–K-24, cross-stage SPARQL checks і regression fixtures |
| Provenance — переважно comments/source fields | Versioned Source/Edition/Location/Interpretation плюс PROV-O derivation model |
| Assessor decision може бути неструктурованим downstream кроком | Selection та AssessorDecision формально відокремлені від derived truth |
| ETCS фактично визначає форму моделі | ETCS не визначає scope ontology й використовується для empirical evaluation |

## Чи все вже оновлено?

**Ні.** Нова система ще не завершена.

- TBox M1–M4 і записана Gate B revision `Payload` проходять OWL 2 DL/HermiT.
- M5 Railway має vocabulary baseline та executable category, threat, criticality, fail-safe, SIL, access і control-weakness slices.
- Новий ETCS ABox структурно мігрований, а synthetic fixtures ростуть разом із rules.
- SHACL K-assets і 45 CQ виконуються; повні P/N/U oracles ще будуються.
- Railway rules працюють через three-valued CriterionEvaluation і run-scoped materialisation.
- Orchestrator та L3 reachability/path/coverage створені; weighted ordering очікує затвердженого методу й factor set.
- ETCS semantic comparison чекає завершення основного M5 pipeline.

Тому старий код зараз залишається **працюючим legacy reference**, а новий репозиторій — **правильно структурованою, але ще незавершеною replacement implementation**.
