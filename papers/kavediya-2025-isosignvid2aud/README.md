# IsoSignVid2Aud reproduction

**Summary.** Not yet determined — assignment established only.

**Paper ID:** `2a405db768a0610bb3c9d6e8806bd44024d8c13c`

**Citation:** Kavediya, H.; Nayak, V.; Sharma, B.; Palaniappan, B. IsoSignVid2Aud: Sign Language Video to Audio Conversion without Text Intermediaries. arXiv:2510.07837, 2025. Presented at the International Conference on AI-ML-Systems (AIMLSystems), 2025.

**Paper:** https://arxiv.org/abs/2510.07837 · **Code/artifacts:** https://github.com/Kugelblitz25/IsoSignVid2Aud (Apache-2.0)

**Preference level:** not yet determined

**Pipeline status:** not yet determined

**Numerical agreement:** not yet determined

**Attempt dates:** 2026-10-01 — , branched from `0ff14a2`

## Reproduction agents

| Agent ID | Model | Application | Contribution |
| --- | --- | --- | --- |
| `reproduction-agent` | Claude Opus 5 (1M context), `claude-opus-5[1m]` | Claude Code 2.1.12 | Assignment establishment only so far |

Identity as reported by the live session; the version is the installation on the executing machine, reached through its VS Code extension.

## Scope and target contract

**Not yet built.** `reproduction.json.targets` is empty.

The export gives `what_to_reproduce` as `"TABLE I and TABLE II \n(and TABLE III? then other metrics and human evaluation?)"`. The parenthetical is the reviewer's own open question, so the requested scope is not yet settled and will be resolved against the paper.

Recorded from the export, to be verified against the paper rather than taken as fact: datasets ASL Citizen and WLASL, both marked `available: yes` and `on_modal: yes`; metrics Accuracy, top-5 accuracy, F1; `copied_scores: yes`, so at least one reported number comes from another paper; `main_experiment_has_ranking: yes`; no human evaluation and no flagged ethical concerns; compute reported as a single NVIDIA RTX A6000 with 48 GB and 4 worker threads. The reviewer notes the experiments use subsets — the 1500 most frequent glosses of ASL Citizen, and the 100 most frequent of WLASL.

## Source provenance

| Artifact | Canonical source | Pinned revision / SHA-256 | Role |
| --- | --- | --- | --- |
| Paper | https://arxiv.org/abs/2510.07837 | not yet pinned | Targets and disclosed protocol |
| Published code | https://github.com/Kugelblitz25/IsoSignVid2Aud | `d4777cfdf41a24bc8c22a41c6d075ebc470c60f0` | Official implementation; Apache-2.0; not yet read or run |
| Author pointer repo | https://github.com/BheeshmSharma/IsoSignVid2Aud_AIMLsystems-2025 | `190e51430cab` | The repository the abstract links to; README only, forwards to the implementation |

**Code is available, contrary to the export.** The export records `code_repos: N/A` and the reviewer noted "No link found in the abstract under 'Code is available at: this link.'". The link is present on the arXiv abstract page, but renders as the text "this https URL", so it is invisible when the abstract is read as plain text. It resolves to the pointer repository above, whose README forwards to the implementation.

`assignment.record` preserves the export verbatim; `assignment.normalized.code_repos` carries the correction, per the contract's rule that normalized "does not override the raw record". The assignee has asked Team S to correct the portal record. A full independent source search has not yet been run.

## Results

Not yet applicable.

## How to repeat this

Not yet applicable — no entry points exist.

## Data provenance and permissions

No data gate has been run. The export marks both datasets `available: yes` and `on_modal: yes`, with ASL Citizen under a "custom Microsoft research license" and WLASL under a "Custom (research only)" licence; neither `permission_to_reproduce` nor `permission_model_weights` is filled in. None of this is verified.

## Environment and patches

Not yet applicable.

## Execution evidence

No runs.

## Guesses and deviations

None yet.

## Attempts, failures, and dead ends

None yet.

## Candidate flags, ethics, and human evaluation

The export records `potential_ethical_concerns: no` and `includes_human_evaluation: no`, and `copied_scores: yes`. These are research leads to investigate, not established facts. The record carries `status: final` set by `goehring@cl.uzh.ch` on 2026-08-18 and no `confirmation` field.

## Author and team contact

None.
