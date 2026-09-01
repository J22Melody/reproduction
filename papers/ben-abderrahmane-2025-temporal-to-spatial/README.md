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

The target paper omits several protocol details but states in §IV that it "adopted the same training parameters as our previous work[19]". Reference [19] (Oulad-Naoui et al., ICEIS 2024, open access) and the ArabSign dataset paper were therefore retrieved and read; both are recorded in `reproduction.json.sources`. They resolve most of the open questions.

**Table III's LSTM column is a copied baseline.** [19] §5 and its conclusion both report a test accuracy of 88.75%, which is exactly Table III's LSTM accuracy of 0.8875. The apparent conflict with §II's citation of "88.5%" dissolves: [19]'s abstract says "surpasses 88.5%" while its body says 88.75%, so both figures trace to [19]. The LSTM column is the prior paper's system rather than a contribution of this paper, so its rows are planned as `not_produced` with reason `copied_baseline`. Note that [19] publishes accuracy only — Table III's LSTM precision (0.8930), recall (0.8875), and F1 (0.8867) appear nowhere in it and are unsourced.

**The label question is resolved.** The portal reviewer noted that the paper never defines its labels, and read the 10-frame samples as windows cut out of sentences. [19] states otherwise: "The mission of the first stage is to convert the input video into a sequence of ten frames", retaining "10×66 numpy vectors corresponding to ten frames per video". Each whole sentence video is therefore downsampled to 10 frames and labelled with which of the 50 sentences it is, giving one sample per video and 9,335 samples. No gloss alignment is required. The target paper's phrase "10 consecutive frames" (§III) contradicts the prior work it says it inherited and is treated as loose wording.

**What remains genuinely unspecified** is how the 10 frames are selected from a video of 39–312 frames. Neither paper states it, and [19] lists the question as future work: "it would be interesting to precisely evaluate the impact of the framing approach on the subsequent stages." A documented sampling choice will be required and recorded under Guesses and deviations.

Documented inconsistencies in the target paper, none of which change the Table III targets:

- **Headline accuracy.** The abstract states the model "achieves 91.3% of accuracy", while Table III reports 0.9777 and §IV describes accuracy stabilising "near 97%". The value 91.3% appears nowhere else. §IV's claim of "nearly 10% of accuracy improvement" reconciles with Table III (0.9777 − 0.8875 = 0.0902) and not with 91.3%.
- **LSTM training time.** Table III reports 3 h; §IV prose says "eight hours for the LSTM model".
- **Training-time comparison is not like-for-like.** [19] ran on an Intel Xeon Silver 4112 with an NVIDIA RTX 4060 GPU, whereas this paper ran CPU-only on an AMD Ryzen 3 4300GE. Table III's "3 h versus 30 mn" therefore compares different hardware, not architectures alone.
- **Table II frame count.** Table II is copied from [19] and labels 200,000 as the total frame count. ArabSign states this figure is "for all sentences performed by one signer"; the label is wrong in both author papers. See Data provenance and permissions.

The portal sub-area "Isolated signing videos" is consistent with this reading: ArabSign is a continuous corpus benchmarked with WER and BLEU over gloss sequences, but both author papers repurpose it as flat 50-way sentence classification.

## Source provenance

| Artifact | Canonical source | Pinned revision / SHA-256 | Role |
| --- | --- | --- | --- |
| Paper PDF | https://doi.org/10.1109/PAIS66004.2025.11126496 | `0afdb6457dbfe7300d6a2c883d06676527bd39ecb658e59c17f48514db9d147c` | Target values and disclosed protocol |
| Prior LSTM paper [19] | https://doi.org/10.2991/978-94-6463-496-9_24 | `c0d48f5e3c2a1ef2c560a7dd2bf36a41f6be7c9207648904720944b1a101a95f` | Inherited preprocessing, 80/20 split, optimizer settings, LSTM architecture, and origin of Table III's copied LSTM accuracy |
| ArabSign dataset paper | https://arxiv.org/abs/2210.03951 | `7be6d45db9a17116201957bae100940d95b0f7fe36cf587b59b6aaa5ea94ccc8` | Authoritative dataset composition, modalities, frame statistics, absence of an official split |
| ArabSign data/code | https://github.com/Hamzah-Luqman/ArabSign | not yet pinned | Access path named by the dataset paper; not yet inspected |
| Published code for this paper | not yet searched | — | — |
| Weights/configs/supplements | not yet searched | — | — |

The target paper's PDF was supplied by the assignee and carries an IEEE Xplore watermark recording download by Northeastern University on 2026-08-01. IEEE Xplore requires a subscription; the PDF is not committed to this repository. Reference [19] is open access under CC BY-NC 4.0 at https://www.atlantis-press.com/article/126002698.pdf and the ArabSign paper is on arXiv; both were retrieved on 2026-08-28 and are likewise referenced by hash rather than committed.

The independent source search required before selecting a preference level has not been run. The portal reviewer confirmed no code repositories are available, which is a lead rather than proof.

## Results

No runs performed. The eight Table III numbers are enumerated as targets; the four LSTM rows are already terminal as copied baselines.

| Target ID | Paper location | System | Dataset/split | Metric + version | Original | Reproduced | Difference | Terminal reason / evidence |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `table3-resnet-accuracy` | Table III, ResNet column, Accuracy | Proposed residual CNN | ArabSign, 80/20 per [19] | Accuracy, version unspecified | 0.9777 | — | — | not yet attempted |
| `table3-resnet-precision` | Table III, ResNet column, Precision | Proposed residual CNN | ArabSign, 80/20 per [19] | Precision, weighted (inferred) | 0.9790 | — | — | not yet attempted |
| `table3-resnet-recall` | Table III, ResNet column, Recall | Proposed residual CNN | ArabSign, 80/20 per [19] | Recall, weighted (inferred) | 0.9777 | — | — | not yet attempted |
| `table3-resnet-f1` | Table III, ResNet column, F1-Score | Proposed residual CNN | ArabSign, 80/20 per [19] | F1, weighted (inferred) | 0.9773 | — | — | not yet attempted |
| `table3-lstm-accuracy` | Table III, LSTM column, Accuracy | Prior LSTM from [19] | ArabSign, 80/20 per [19] | Accuracy, version unspecified | 0.8875 | — | — | `copied_baseline`: equals [19]'s reported 88.75% test accuracy exactly |
| `table3-lstm-precision` | Table III, LSTM column, Precision | Prior LSTM from [19] | ArabSign, 80/20 per [19] | Precision, weighted (inferred) | 0.8930 | — | — | `copied_baseline`: [19]'s column; this value is not published in [19] |
| `table3-lstm-recall` | Table III, LSTM column, Recall | Prior LSTM from [19] | ArabSign, 80/20 per [19] | Recall, weighted (inferred) | 0.8875 | — | — | `copied_baseline`: [19]'s column; this value is not published in [19] |
| `table3-lstm-f1` | Table III, LSTM column, F1-Score | Prior LSTM from [19] | ArabSign, 80/20 per [19] | F1, weighted (inferred) | 0.8867 | — | — | `copied_baseline`: [19]'s column; this value is not published in [19] |

The entire LSTM column is reference [19]'s system rather than a contribution of this paper, so all four of its rows are recorded as `not_produced` with reason `copied_baseline` and are not reproduced under this assignment. Only the accuracy row is verifiably copied: [19] reports accuracy alone, so its precision, recall, and F1 values are unsourced and their origin cannot be recovered from either paper.

Table III also reports Model Size, Total Parameters, and Training Time. The portal requested Accuracy, Precision, Recall, and F1, so those three rows are out of scope as targets; the parameter counts are noted under Scope and the training-time comparison is recorded there as an inconsistency.

Pipeline completeness and numerical agreement are separate and neither is yet determined.

## How to repeat this

Not yet applicable — no entry points exist.

## Data provenance and permissions

| Dataset | Version/subset/splits | Source and access date | License/permission and cloud-use basis | Path in Volume `datasets` | Counts / manifest / checksum | Deviations |
| --- | --- | --- | --- | --- | --- | --- |
| ArabSign | Full release; no official train/test split exists | Paper read 2026-08-28; data not yet retrieved from https://github.com/Hamzah-Luqman/ArabSign | unverified | not yet checked | 9,335 samples claimed by both papers; not yet verified | none yet |

**No data gate has been run.** Availability, licence, cloud-processing basis, expected counts, and presence under the shared `datasets` Volume are all unverified. The table above records only what the ArabSign paper states.

From the ArabSign paper (Luqman, FG 2023 / arXiv:2210.03951), relevant to the eventual gate:

- 9,335 samples representing 50 sentences, performed by 6 signers, each sentence repeated at least 30 times per signer.
- Recorded with Kinect V2 in three simultaneous modalities: colour 1920×1080 at 30 fps, depth 512×424, and skeleton joint points. The target paper uses MediaPipe pose on frames, so it consumes the colour modality rather than the provided skeleton data.
- Video duration ranges from 1.3 s to 10.4 s; average sentence length 3.1 signs; vocabulary 95 signs across 155 signs in total.
- "This resulted in around 200,000 frames for all sentences performed by **one signer**, with an average of 130.3 frames per sentence." This reconciles the arithmetic that Table II of both author papers appears to contradict: 9,335 / 6 ≈ 1,556 samples per signer × 130.3 ≈ 203,000 frames.
- **ArabSign publishes no fixed split.** Its own benchmark states only that it "combined all signers' samples and split them into training and testing", with no ratio, seed, or file lists. [19] used "the common 80/20 data split", so the split is the authors' own choice and its exact composition is unrecoverable.
- All 6 signers are male, aged 21–30, right-handed, one wearing eyeglasses, recorded in an unconstrained room with a white background. Identifiability, consent basis, and cloud-processing rights therefore still require examination at the data gate.

## Environment and patches

Not yet applicable. No container, dependencies, or patches defined.

## Execution evidence

No runs. No Modal resources created.

## Guesses and deviations

| Detail | Paper/evidence says | This attempt used | Rationale | Effect on interpretation |
| --- | --- | --- | --- | --- |
| Precision/recall/F1 averaging | Not stated in either paper | Support-weighted average over the 50 classes | Table III reports Recall exactly equal to Accuracy in both columns (0.9777 and 0.8875). Support-weighted recall is identically equal to accuracy; macro and micro averaging are not | If the authors in fact used macro averaging, the three reproduced values shift. Classes are near-balanced at roughly 187 samples each, so the divergence should be small |
| Train/test split | Target paper silent; [19] §5 says "the common 80/20 data split"; ArabSign publishes no official split | 80/20 over all 9,335 samples | §IV states the training parameters were adopted from [19] | Seed and exact composition are unrecoverable, so sample-level agreement cannot be expected. The split is signer-dependent by construction, so no signer-independent claim follows |
| Learning rate | Target paper does not state it; [19] §5 states 0.001 | 0.001 | §IV: "same training parameters as our previous work[19]" | Low risk; the remaining optimizer settings are stated identically in both papers |

Still to be decided before implementation: **which 10 frames** are taken from each video. Videos run 1.3–10.4 s at 30 fps (39–312 frames), and neither paper states the selection rule — [19] lists it as future work. A documented sampling choice will be added here.

## Attempts, failures, and dead ends

None yet.

## Candidate flags, ethics, and human evaluation

The portal record carries ethics, human-evaluation, and copied-score fields, but their radio values did not survive transcription and are recorded as `null`; their absence here is a gap in our copy, not a clearance. Obtaining the machine export would resolve them.

The paper reports no human evaluation. §III notes the ArabSign dataset comprises videos of identifiable male signers aged 21–30 recorded in consistent environments, so identifiability, consent basis, and cloud-processing rights must be examined at the data gate.

## Author and team contact

None.
