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
| `reproduction-agent` | Claude Opus 5 (1M context), `claude-opus-5[1m]` | Claude Code 2.1.12 | Assignment establishment |
| `reproduction-agent-opus-5-5` | Claude Opus 5.5, `claude-opus-5-5` | Claude Code 2.1.12 | Target contract onward |

Identities as reported by the live session; the model was switched mid-attempt on 2026-10-01, so both are kept. The version is the installation on the executing machine, reached through its VS Code extension.

## Scope and target contract

**35 targets: 24 in scope, 11 copied baselines.** The export's `what_to_reproduce` left its own question open — "TABLE I and TABLE II (and TABLE III? then other metrics and human evaluation?)" — and the assignee resolved it to three experiments (gate `scope-what-to-reproduce`). The paper has no human evaluation.

| Experiment | Source | In scope | Copied |
| --- | --- | ---: | ---: |
| Isolated sign recognition, ASL-Citizen-1500 | Table I: Top-1, Top-5, F1 for I3D, IsoSignVid2Aud, combined training | 9 | 0 |
| Isolated sign recognition, WLASL-100 | Table II: Top-1, Top-5 for the two IsoSignVid2Aud variants | 4 | 11 |
| Audio generation, WLASL-100 | Table III: PESQ, STOI, SNR, "MSE" for both variants | 8 | 0 |
| Sequence translation, ASL Citizen | §V.A prose: WER 0.3000, CER 0.2733, BLEU 0.7036 | 3 | 0 |

**The task is isolated sign recognition with an audio head.** The I3D extractor has an explicit classification head (1500 or 100 classes, cross-entropy), and the combined objective is `L_cls + 2·L_spec`. Top-1, Top-5 and F1 come straight from the classifier logits. The spectrogram generator maps the 2048-d I3D feature to a complex spectrogram, inverted by ISTFT; its training target for every video of a class is a TTS rendering of that class's gloss, so "without text intermediaries" holds at inference only.

**Table I's I3D row is not copied.** It cites [6], but ASL Citizen reports I3D at 63.10% on the full 2,731 classes and 74.16% on its own WLASL-overlap subset; 71.10 / 90.13 / 0.70 appears nowhere in it. It is treated as the authors' own run on their 1,500-gloss subset, and it is needed to support the paper's claimed +0.91% over I3D. Table II's cited rows are copied; the I3D one is verified against WLASL [18] (65.89 / 84.11).

**The ASL Citizen subset is unexplained.** The paper restricts ASL Citizen to its 1,500 most frequent glosses without giving a reason. Since I3D was re-run on the same subset, Table I's internal comparison is consistent; but the "[6]" citation implies a published figure, and no Table I number is comparable with other ASL Citizen results. The subset is reproduced as the authors defined it.

**IsoSignVid2Aud's recogniser is I3D with a modified head.** The base is `pytorchvideo`'s Kinetics-pretrained `i3d_r50`, the final block replaced by a 4×7×7 average pool, then dropout 0.5, a linear layer to the class count, and a **ReLU on the logits**, which zeroes every negative class score before cross-entropy. Training adds five augmented copies of each video (colour jitter, ±15° rotation, up to ⅛ of frames dropped). The paper does not say how its I3D baseline was trained, so whether the +0.91% comes from the head or from the augmentation is untested.

**The two variants differ in training, not architecture.** *IsoSignVid2Aud* is trained sequentially: the extractor on classification alone, then frozen while its features train the spectrogram generator. *Combined training* optimises both jointly under `L_cls + 2·L_spec`, so the spectrogram loss backpropagates into the extractor — which is why it reports different recognition accuracy (75.19 vs 72.01 on ASL Citizen, 77.72 vs 78.67 on WLASL-100). Since each class's spectrogram target is a fixed TTS clip, that extra loss is effectively a second per-class signal.

### Discrepancies tracked

None of these blocks the work; they are recorded as found.

| Where | Paper says | Code or source says |
| --- | --- | --- |
| How Top-1/Top-5 are measured | §IV.J: "by transcribing the audio" | `extractor/test.py`: from classifier logits; transcription is used only in the sequence experiment |
| TTS for training targets | §III.C: Tacotron2 | `spec_gen.py`: gTTS (`tld="co.in"`), an unpinned network service |
| Backbone | §III.B: Inception-based I3D | `extractor/model.py`: `i3d_r50`, a ResNet-50 I3D |
| Extractor batch size | §IV.E, §IV.I: 4 | `config.yaml`: 3 |
| NMS window / hop | §IV.I: 50 / 3 | `config.yaml`: 45 / 5, plus overlap 5 |
| Shipped config | ASL-Citizen-1500 and WLASL-100 | `config.yaml`: `n_words: 100` on ASL Citizen, checkpoints `asl-citizen-100` — matching no reported experiment |
| Sequence-experiment ASR | unnamed | `test.py`: Whisper large, `nltk` BLEU with smoothing method 4, `jiwer` WER/CER |
| Table III "MSE" | mean squared error | `transformer/test.py` line 221: MAE of the final test sample only (gate `table3-mse-definition`, resolved: run both) |
| Table II I3D attribution | [4], the original I3D paper | number is from WLASL [18] |
| Table I I3D attribution | [6] | number is not in [6] |
| PESQ | abstract 2.67 | Table III 2.68 |
| PESQ range | §IV.J −0.5 to 4.5 | Table III footnote 1 to 5; code uses wideband PESQ |
| Metrics | export lists F1 | Table II has no F1 column |

**Latent label-mapping risk, to check at the data gate.** `verify.py` calls `create_subset` separately on train, test and val, so each split selects its own top-N glosses from its own counts; `extractor/dataset.py` then indexes labels by each split's own sorted vocabulary. If the per-split vocabularies differ by even one gloss, every later index shifts and predictions are scored against a different mapping. It is harmless if they coincide, which is checkable from the CSVs alone. The same code also means WLASL-100 is selected by per-split frequency rather than from WLASL's official 100-class definition, which bears on Table II's comparison with copied baselines.

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
