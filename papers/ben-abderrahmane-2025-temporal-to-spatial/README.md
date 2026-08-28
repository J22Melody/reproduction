# Temporal-to-Spatial ArSL ResNet reproduction

**Paper ID:** `8b224ecbd42da766efba45d17b34b3a1255c2345`

**Citation:** Ben-Abderrahmane, H.; Oulad-Naoui, S.; Cherif, A.; Chagha, A. Temporal-to-Spatial Transmutation for Enhancing Arabic Sign Language Recognition via ResNet. In *2025 7th International Conference on Pattern Analysis and Intelligent Systems (PAIS)*, IEEE, 2025. doi:10.1109/PAIS66004.2025.11126496.

**Paper:** https://doi.org/10.1109/PAIS66004.2025.11126496 · **Code/artifacts:** the portal reviewer confirmed no code repositories are available; an independent source search is still pending and that confirmation is not treated as proof

**Preference level:** not yet determined

**Status:** not yet determined — assignment established only

**Attempt date:** 2026-08-28 (branched from `4894d7e`)

## Scope and target contract

**Not yet built.** `reproduction.json.targets` is empty; the target contract is the next stage.

The assignment was made through the REPRO-SIGN portal. No machine-readable candidate export was available, so the portal record was transcribed by hand into `assignment.normalized` and is marked as a transcription rather than an export. `assignment.kind` therefore remains `direct_user_request`, and no `assignment.record` is claimed. Radio-button fields — including `copied_scores`, `potential_ethical_concerns`, `includes_human_evaluation`, and the record's own `confirmation`/`status` — did not render their values and are recorded as `null` rather than guessed. The form still offered Finalize / Flag / Reject, so whether this record is `confirmed` and `final` is unverified.

The portal states **What to Reproduce: "Table 3"**, with metrics Accuracy, Precision, Recall, and F1. Those are exactly the rows of the paper's TABLE III (Model Comparison), which is read here as the requested table. Its two columns are the proposed ResNet system (Accuracy 0.9777, Precision 0.9790, Recall 0.9777, F1 0.9773) and an LSTM comparison (0.8875, 0.8930, 0.8875, 0.8867).

Two discrepancies must be settled while building the ledger:

- **Headline accuracy conflict.** The abstract states the model "achieves 91.3% of accuracy", while Table III reports 0.9777 and §IV describes accuracy stabilising "near 97%". The value 91.3% appears nowhere else in the paper. Under the Table III scope it is not a target, but it is recorded here as a documented internal inconsistency.
- **LSTM column provenance.** Table III's LSTM accuracy is 0.8875, while §II cites the authors' earlier LSTM work [19] as achieving 88.5%. Whether that column is a copied baseline or a re-run is unresolved, and the portal's `copied_scores` value was not readable.

**Open protocol question carried from the portal reviewer:** *"paper does not mention what the labels are: data used are sentences, authors mention samples of 10 frames (presumably cut out of the sentences) but nothing about gloss alignment."* ArabSign contains 9,335 samples of 50 continuous sentences (average length 3.1, ~130 frames per sentence), yet the model input is `(10, 33, 2)` — 10 frames — with a 50-way output. How a 10-frame window inherits a sentence label is not stated, and different readings give materially different experiments. Note also that the portal sub-area is "Isolated signing videos" while ArabSign is a continuous corpus. This is expected to become a target/protocol gate before any implementation work.

## Source provenance

| Artifact | Canonical source | Pinned revision / SHA-256 | Role |
| --- | --- | --- | --- |
| Paper PDF | https://doi.org/10.1109/PAIS66004.2025.11126496 | `0afdb6457dbfe7300d6a2c883d06676527bd39ecb658e59c17f48514db9d147c` | Target values and disclosed protocol |
| Published code | not yet searched | — | — |
| Weights/configs/supplements | not yet searched | — | — |

The PDF was supplied by the assignee and carries an IEEE Xplore watermark recording download by Northeastern University on 2026-08-01. IEEE Xplore requires a subscription; the PDF is not committed to this repository.

## Results

No targets defined and no runs performed.

## How to repeat this

Not yet applicable — no entry points exist.

## Data provenance and permissions

The paper evaluates on the ArabSign dataset (Luqman, *ArabSign: A Multi-modality Dataset and Benchmark for Continuous Arabic Sign Language Recognition*, FG 2023). No data gate has been run; availability, license, cloud-processing basis, and presence under the shared `datasets` Volume are all unverified.

## Environment and patches

Not yet applicable. No container, dependencies, or patches defined.

## Execution evidence

No runs. No Modal resources created.

## Guesses and deviations

None yet.

## Attempts, failures, and dead ends

None yet.

## Candidate flags, ethics, and human evaluation

The portal record carries ethics, human-evaluation, and copied-score fields, but their radio values did not survive transcription and are recorded as `null`; their absence here is a gap in our copy, not a clearance. Obtaining the machine export would resolve them.

The paper reports no human evaluation. §III notes the ArabSign dataset comprises videos of identifiable male signers aged 21–30 recorded in consistent environments, so identifiability, consent basis, and cloud-processing rights must be examined at the data gate.

## Author and team contact

None.
