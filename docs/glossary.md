# Glossary

Daksh process terms used across pipeline documents.

## PTL

Project Technical Lead. The delivery-team person accountable for the overall technical execution of a project within the Daksh pipeline. Every manifest has exactly one PTL listed in `team_roster`.

## Open Question

A named, unresolved question that blocks one or more downstream decisions, milestones, or goals. In Daksh, Open Questions are first-class entities: they appear in the cognition graph, are explicitly tracked per stage, and must either be resolved (a Decision `decides` them) or acknowledged as blocking (they `threaten` what they block).

## Unvalidated Assumption

A belief the project design depends on that has not been tested with real users, data, or experiments. Daksh mandates at least one Unvalidated Assumption section per onboarding document. Each assumption includes a validation plan — how the team would discover if the assumption is false.

## Weight Class

A project's size classification in the Daksh pipeline: `small`, `medium`, or `large`. Determined at init by timeline and module count. Controls approval count per gate, Jira sync policy, open questions policy, and tend frequency.

## Stage

A named phase in the Daksh pipeline with a defined output document, approval gate, and cognition graph. Stages are sequentially numbered (00, 10, 20, 30, 35, 40a–40d, 50, 60). Small projects may combine stages (e.g. `00+10`) or merge module-band stages (e.g. `40a+40c`).

## Cognition Graph

An interactive, entity-typed graph produced by every Daksh stage and embedded in the stage's output document. The graph answers one stated question per stage. It is not decoration — it is the primary cognition surface for readers who need to understand structure without reading prose sequentially.
