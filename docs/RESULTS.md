# Results

SYNTHETIC toy; not a medical model, not a medical device, not a diagnosis. Every number below is a property of a seeded simulation of random heart-shaped layouts, a synthetic wave, synthetic noise and synthetic out-of-library fields. Nothing here transfers to real physiology or real data. Generated from `docs/results/confirm.json` by `python -m experiments.render_results`; do not edit by hand (hand-written interpretation is in `docs/interpretation.md`).

Protocol: `docs/PROTOCOL.md`, committed before any result existed (amendment A1 was committed before the confirmation run). Confirmation set: seeds 5000 to 5199 (200 replicates), run once. Development set: seeds 1000 to 1199. Intervals are 95 % percentile bootstrap over replicates (5000 resamples); proportions in brackets after the text `Wilson` are pooled-trial Wilson intervals and understate uncertainty. Package version 0.1.0; produced with Python 3.13.5.

## 1. Pre-registered hypotheses (confirmation seeds)

| id | statement | mean [95% CI] | test | Holm p | outcome | dev mean |
|---|---|---|---|---|---|---|
| H1 | recognition accuracy at sigma 0.15 exceeds 0.90 | 0.9995 [0.9991, 0.9998] | greater vs 0.9 | 0.0009 | supported | 0.9997 |
| H2 | Haar-field refusal at sigma 0.15 (matched calibration) exceeds 0.90 | 0.9955 [0.9939, 0.9970] | greater vs 0.9 | 0.0009 | supported | 0.9962 |
| H3 | label-shuffled recognition equals chance (0.25) | 0.2464 [0.2405, 0.2522] | two-sided vs 0.25 | 0.2423 | control passes (consistent with chance) | 0.2486 |
| H4 | pure phase wave: recognition accuracy at sigma 0.15 is below 0.40 | 0.2505 [0.2467, 0.2546] | less vs 0.4 | 0.0009 | supported | 0.2502 |
| H5 | max-overlap gate AUC against scrambled-phase fields exceeds 0.90 | 1.0000 [1.0000, 1.0000] | greater vs 0.9 | 0.0009 | supported | 1.0000 |
| H6 | max-overlap gate AUC beats wave_scan on waves between stored phases | 0.0762 [0.0682, 0.0846] | greater vs 0.0 | 0.0009 | supported | 0.0760 |
| H7 | balanced accuracy vs Haar differs between midpoint and first-best tau | 0.0022 [0.0013, 0.0031] | two-sided vs 0.0 | 0.0009 | supported | 0.0021 |
| H8 | a globally phase-rotated stored wave is accepted (>0.99): known blind spot | 0.0000 [0.0000, 0.0000] | less vs 0.01 | 0.0009 | supported | 0.0000 |
| H9 | a wave between stored phases is refused less than half the time | 0.0000 [0.0000, 0.0000] | less vs 0.5 | 0.0009 | supported | 0.0000 |

Holm p is adjusted over the nine hypotheses together; H3 is a null-retention control (amendment A2). A supported hypothesis is a statement about this simulation only; effect size is in the mean column and must be read with it (H7 is supported yet tiny; H6 compares two AUCs that are both far below 0.5).

## 2. Study A: recognition and refusal across noise

| sigma | acc ungated | acc gated | accept in-library | refuse Haar | refuse scrambled phase | tau | J cal |
|---|---|---|---|---|---|---|---|
| 0.00 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.658 | 1.000 |
| 0.05 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.569 | 1.000 |
| 0.10 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.428 | 1.000 |
| 0.15 | 1.000 [0.999, 1.000] | 0.996 [0.995, 0.997] | 0.997 [0.996, 0.998] | 0.996 [0.994, 0.997] | 0.998 [0.997, 0.999] | 0.331 | 0.998 |
| 0.20 | 0.992 [0.991, 0.994] | 0.962 [0.959, 0.965] | 0.967 [0.964, 0.970] | 0.968 [0.964, 0.973] | 0.979 [0.976, 0.983] | 0.276 | 0.954 |
| 0.30 | 0.901 [0.896, 0.905] | 0.770 [0.762, 0.779] | 0.821 [0.813, 0.830] | 0.870 [0.861, 0.880] | 0.889 [0.881, 0.898] | 0.228 | 0.722 |
| 0.45 | 0.694 [0.688, 0.701] | 0.502 [0.492, 0.512] | 0.642 [0.629, 0.656] | 0.741 [0.727, 0.756] | 0.767 [0.752, 0.782] | 0.201 | 0.431 |
| 0.60 | 0.545 [0.539, 0.552] | 0.360 [0.350, 0.371] | 0.571 [0.553, 0.590] | 0.666 [0.647, 0.685] | 0.686 [0.668, 0.705] | 0.189 | 0.276 |

Chance for four phases is 0.25. The gate is calibrated at the same sigma as the evaluation (matched). Pooled Wilson interval for the sigma 0.15 ungated accuracy: [0.999, 1.000].

## 3. Study B: ablations (paired with the default by seed)

### sigma 0.15

| variant | acc ungated | difference vs default | Holm p (exploratory) | acc gated | J cal | max neighbour overlap |
|---|---|---|---|---|---|---|
| default | 1.000 [0.999, 1.000] | (default) |  | 0.996 | 0.998 | 0.489 |
| envelope_off | 0.251 [0.247, 0.255] | -0.749 [-0.753, -0.745] | 0.0084 | 0.250 | 0.999 | 1.000 |
| width_2 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.001] | 0.1008 | 0.997 | 0.997 | 0.000 |
| width_4 | 1.000 [1.000, 1.000] | 0.001 [0.000, 0.001] | 0.1008 | 0.996 | 0.998 | 0.038 |
| width_6 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.001] | 0.1440 | 0.996 | 0.998 | 0.240 |
| width_12 | 0.986 [0.984, 0.988] | -0.013 [-0.015, -0.012] | 0.0084 | 0.983 | 0.997 | 0.779 |
| width_16 | 0.950 [0.946, 0.955] | -0.049 [-0.054, -0.045] | 0.0084 | 0.947 | 0.997 | 0.883 |
| width_24 | 0.828 [0.821, 0.835] | -0.171 [-0.179, -0.164] | 0.0084 | 0.826 | 0.998 | 0.961 |
| width_64 | 0.353 [0.347, 0.359] | -0.647 [-0.653, -0.640] | 0.0084 | 0.352 | 0.999 | 0.999 |
| phases_6 | 0.981 [0.978, 0.985] (chance 0.167) | -0.018 [-0.022, -0.015] | 0.0084 | 0.977 | 0.998 | 0.790 |
| phases_8 | 0.951 [0.945, 0.957] (chance 0.125) | -0.049 [-0.054, -0.043] | 0.0084 | 0.946 | 0.997 | 0.908 |
| n_32 | 1.000 [0.999, 1.000] | 0.000 [0.000, 0.001] | 1.0000 | 0.995 | 0.997 | 0.429 |
| n_128 | 0.999 [0.998, 0.999] | -0.001 [-0.002, 0.000] | 0.1216 | 0.996 | 0.998 | 0.546 |
| n_32_snr | 0.991 [0.989, 0.992] | -0.009 [-0.010, -0.007] | 0.0084 | 0.949 | 0.925 | 0.429 |
| n_128_snr | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.001] | 0.4185 | 1.000 | 1.000 | 0.546 |
| k_2 | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.001] | 0.8358 | 0.996 | 0.998 | 0.357 |
| k_3 | 1.000 [0.999, 1.000] | 0.000 [0.000, 0.000] | 1.0000 | 0.996 | 0.997 | 0.453 |
| k_6 | 0.999 [0.999, 1.000] | 0.000 [-0.001, 0.000] | 1.0000 | 0.996 | 0.997 | 0.508 |
| k_8 | 0.999 [0.998, 0.999] | -0.001 [-0.001, 0.000] | 0.4343 | 0.995 | 0.997 | 0.553 |
| pace_bottom | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.001] | 1.0000 | 0.996 | 0.997 | 0.363 |
| pace_left_lobe | 1.000 [0.999, 1.000] | 0.000 [0.000, 0.001] | 1.0000 | 0.996 | 0.997 | 0.380 |
| pace_centre | 0.999 [0.999, 1.000] | 0.000 [-0.001, 0.000] | 1.0000 | 0.995 | 0.998 | 0.471 |

### sigma 0.30

| variant | acc ungated | difference vs default | Holm p (exploratory) | acc gated | J cal | max neighbour overlap |
|---|---|---|---|---|---|---|
| default | 0.901 [0.896, 0.905] | (default) |  | 0.770 | 0.722 | 0.489 |
| envelope_off | 0.252 [0.247, 0.257] | -0.649 [-0.656, -0.642] | 0.0084 | 0.226 | 0.827 | 1.000 |
| width_2 | 0.923 [0.920, 0.926] | 0.022 [0.018, 0.027] | 0.0084 | 0.791 | 0.704 | 0.000 |
| width_4 | 0.921 [0.918, 0.925] | 0.021 [0.017, 0.025] | 0.0084 | 0.789 | 0.705 | 0.038 |
| width_6 | 0.919 [0.916, 0.923] | 0.019 [0.016, 0.022] | 0.0084 | 0.783 | 0.711 | 0.240 |
| width_12 | 0.828 [0.822, 0.834] | -0.072 [-0.077, -0.068] | 0.0084 | 0.716 | 0.743 | 0.779 |
| width_16 | 0.744 [0.737, 0.751] | -0.157 [-0.162, -0.151] | 0.0084 | 0.649 | 0.766 | 0.883 |
| width_24 | 0.566 [0.559, 0.574] | -0.334 [-0.341, -0.328] | 0.0084 | 0.505 | 0.798 | 0.961 |
| width_64 | 0.298 [0.292, 0.304] | -0.603 [-0.609, -0.596] | 0.0084 | 0.268 | 0.826 | 0.999 |
| phases_6 | 0.825 [0.819, 0.831] (chance 0.167) | -0.075 [-0.082, -0.069] | 0.0084 | 0.707 | 0.705 | 0.790 |
| phases_8 | 0.753 [0.746, 0.760] (chance 0.125) | -0.148 [-0.155, -0.141] | 0.0084 | 0.643 | 0.688 | 0.908 |
| n_32 | 0.906 [0.902, 0.910] | 0.006 [0.000, 0.012] | 0.4817 | 0.779 | 0.703 | 0.429 |
| n_128 | 0.898 [0.894, 0.902] | -0.003 [-0.009, 0.004] | 1.0000 | 0.773 | 0.722 | 0.546 |
| n_32_snr | 0.731 [0.725, 0.737] | -0.170 [-0.177, -0.162] | 0.0084 | 0.551 | 0.448 | 0.429 |
| n_128_snr | 0.983 [0.981, 0.985] | 0.082 [0.077, 0.087] | 0.0084 | 0.945 | 0.938 | 0.546 |
| k_2 | 0.911 [0.907, 0.915] | 0.010 [0.005, 0.016] | 0.0084 | 0.783 | 0.714 | 0.357 |
| k_3 | 0.907 [0.903, 0.911] | 0.006 [0.002, 0.011] | 0.0760 | 0.773 | 0.716 | 0.453 |
| k_6 | 0.901 [0.897, 0.906] | 0.001 [-0.004, 0.005] | 1.0000 | 0.780 | 0.724 | 0.508 |
| k_8 | 0.900 [0.896, 0.905] | 0.000 [-0.005, 0.004] | 1.0000 | 0.774 | 0.723 | 0.553 |
| pace_bottom | 0.912 [0.908, 0.917] | 0.012 [0.007, 0.017] | 0.0084 | 0.779 | 0.716 | 0.363 |
| pace_left_lobe | 0.911 [0.907, 0.915] | 0.010 [0.004, 0.016] | 0.0280 | 0.777 | 0.719 | 0.380 |
| pace_centre | 0.907 [0.903, 0.912] | 0.007 [0.001, 0.013] | 0.2603 | 0.787 | 0.718 | 0.471 |

`n_32_snr` and `n_128_snr` scale sigma by sqrt(64/n); `n_32` and `n_128` keep the same absolute sigma. Holm p is exploratory and adjusted over all ablation differences at both sigmas together.

## 4. Study C: refusal quality and baselines

AUC treats in-library probes (noisy, sigma 0.15) as positive and out-of-library probes as negative; 0.5 is no separation and values below 0.5 mean the out-of-library probes score HIGHER than in-library ones. The trivial `constant` gate has AUC 0.5 and balanced accuracy 0.5 by construction. Out-of-library probes in this first table are noise-free.

### AUC and balanced accuracy, noise-free out-of-library probes (pre-registered)

| kind | AUC max_overlap | AUC wave_scan | AUC magnitude_profile | bal acc max_overlap | bal acc wave_scan | bal acc magnitude_profile |
|---|---|---|---|---|---|---|
| haar | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.709 [0.692, 0.726] | 0.996 | 0.994 | 0.686 |
| phase_scramble | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.336 [0.309, 0.364] | 0.997 | 0.995 | 0.283 |
| phase_scramble_envelope | 0.850 [0.835, 0.865] | 0.845 [0.830, 0.859] | 0.000 [0.000, 0.000] | 0.859 | 0.845 | 0.261 |
| magnitude_permuted | 0.623 [0.609, 0.637] | 0.459 [0.449, 0.470] | 0.985 [0.983, 0.988] | 0.522 | 0.503 | 0.759 |
| time_shift_half_spacing | 0.076 [0.068, 0.085] | 0.000 [0.000, 0.000] | 0.514 [0.498, 0.529] | 0.498 | 0.497 | 0.513 |
| time_shift_quarter_spacing | 0.155 [0.140, 0.170] | 0.000 [0.000, 0.000] | 0.241 [0.227, 0.256] | 0.498 | 0.497 | 0.372 |
| partial_random_half | 0.026 [0.024, 0.029] | 0.011 [0.010, 0.013] | 0.422 [0.415, 0.430] | 0.498 | 0.497 | 0.470 |
| partial_late_half | 0.114 [0.098, 0.130] | 0.069 [0.055, 0.084] | 0.380 [0.358, 0.403] | 0.511 | 0.511 | 0.448 |
| stored_plus_noise_0.6 | 1.000 [1.000, 1.000] | 0.999 [0.999, 1.000] | 0.711 [0.693, 0.728] | 0.983 | 0.983 | 0.684 |
| stored_plus_noise_1.0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.709 [0.692, 0.727] | 0.993 | 0.992 | 0.683 |
| conjugate_wave | 0.135 [0.116, 0.155] | 0.067 [0.055, 0.079] | 0.000 [0.000, 0.000] | 0.502 | 0.497 | 0.261 |
| global_phase_rotation | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.498 | 0.497 | 0.261 |

### AUC and balanced accuracy, noise-matched out-of-library probes (sigma 0.15; exploratory, amendment A1)

| kind | AUC max_overlap | AUC wave_scan | AUC magnitude_profile | bal acc max_overlap | bal acc wave_scan | bal acc magnitude_profile |
|---|---|---|---|---|---|---|
| haar | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.711 [0.693, 0.728] | 0.997 | 0.995 | 0.686 |
| phase_scramble | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.700 [0.683, 0.718] | 0.997 | 0.994 | 0.679 |
| phase_scramble_envelope | 0.986 [0.983, 0.988] | 0.986 [0.983, 0.989] | 0.499 [0.493, 0.504] | 0.942 | 0.945 | 0.500 |
| magnitude_permuted | 0.992 [0.991, 0.993] | 0.983 [0.981, 0.984] | 0.746 [0.730, 0.761] | 0.865 | 0.817 | 0.701 |
| time_shift_half_spacing | 0.873 [0.864, 0.882] | 0.497 [0.490, 0.503] | 0.654 [0.638, 0.670] | 0.655 | 0.499 | 0.604 |
| time_shift_quarter_spacing | 0.806 [0.798, 0.813] | 0.532 [0.525, 0.540] | 0.654 [0.642, 0.665] | 0.614 | 0.501 | 0.598 |
| partial_random_half | 0.912 [0.908, 0.916] | 0.896 [0.892, 0.901] | 0.562 [0.553, 0.572] | 0.648 | 0.642 | 0.539 |
| partial_late_half | 0.797 [0.790, 0.805] | 0.685 [0.676, 0.693] | 0.616 [0.609, 0.624] | 0.641 | 0.563 | 0.594 |
| stored_plus_noise_0.6 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.713 [0.696, 0.730] | 0.995 | 0.992 | 0.686 |
| stored_plus_noise_1.0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.711 [0.693, 0.727] | 0.996 | 0.993 | 0.687 |
| conjugate_wave | 0.955 [0.949, 0.960] | 0.942 [0.937, 0.948] | 0.493 [0.486, 0.499] | 0.727 | 0.695 | 0.498 |
| global_phase_rotation | 0.495 [0.488, 0.502] | 0.495 [0.488, 0.502] | 0.496 [0.489, 0.502] | 0.500 | 0.500 | 0.497 |

### tau rules, held-out balanced accuracy (sigma 0.15)

| rule | mean tau | accept in-library | bal acc vs Haar | bal acc vs scrambled phase |
|---|---|---|---|---|
| midpoint | 0.331 | 0.997 [0.996, 0.998] | 0.9961 [0.9953, 0.9969] | 0.9973 [0.9968, 0.9979] |
| first | 0.312 | 0.998 [0.998, 0.999] | 0.9940 [0.9928, 0.9951] | 0.9960 [0.9952, 0.9969] |
| midpoint_all | 0.331 | 0.997 [0.996, 0.998] | 0.9962 [0.9953, 0.9970] | 0.9973 [0.9967, 0.9979] |
| median | 0.331 | 0.997 [0.996, 0.998] | 0.9962 [0.9953, 0.9971] | 0.9973 [0.9967, 0.9979] |

Paired differences (midpoint minus other), balanced accuracy vs Haar: first: 0.0022 [0.0013, 0.0031]; midpoint_all: -0.0001 [-0.0002, 0.0001]; median: -0.0001 [-0.0003, 0.0001].

## 5. Study D: negative controls and out-of-library kinds

Label-shuffled recognition (chance 0.25): 0.2464 [0.2405, 0.2522]. In-library acceptance of the frozen gate: 0.997 [0.996, 0.998].

Classification rule (pre-registered): REFUSED at mean refusal 0.90 or more, NOT REFUSED below 0.10, otherwise PARTLY REFUSED.

| kind | refusal (noise-free) | class | mean max overlap | refusal (noise-matched) | class | mean max overlap |
|---|---|---|---|---|---|---|
| haar | 0.996 [0.994, 0.997] | REFUSED | 0.171 | 0.996 [0.995, 0.998] | REFUSED | 0.170 |
| phase_scramble | 0.998 [0.997, 0.999] | REFUSED | 0.168 | 0.997 [0.995, 0.998] | REFUSED | 0.171 |
| phase_scramble_envelope | 0.721 [0.709, 0.734] | PARTLY REFUSED | 0.288 | 0.888 [0.875, 0.901] | PARTLY REFUSED | 0.207 |
| magnitude_permuted | 0.047 [0.041, 0.055] | NOT REFUSED | 0.479 | 0.734 [0.718, 0.750] | PARTLY REFUSED | 0.286 |
| time_shift_half_spacing | 0.000 [0.000, 0.000] | NOT REFUSED | 0.717 | 0.314 [0.299, 0.328] | PARTLY REFUSED | 0.381 |
| time_shift_quarter_spacing | 0.000 [0.000, 0.000] | NOT REFUSED | 0.777 | 0.232 [0.219, 0.245] | PARTLY REFUSED | 0.408 |
| partial_random_half | 0.000 [0.000, 0.000] | NOT REFUSED | 0.717 | 0.299 [0.284, 0.313] | PARTLY REFUSED | 0.375 |
| partial_late_half | 0.024 [0.014, 0.036] | NOT REFUSED | 0.761 | 0.285 [0.269, 0.302] | PARTLY REFUSED | 0.400 |
| stored_plus_noise_0.6 | 0.969 [0.965, 0.974] | REFUSED | 0.204 | 0.993 [0.991, 0.995] | REFUSED | 0.179 |
| stored_plus_noise_1.0 | 0.990 [0.988, 0.992] | REFUSED | 0.184 | 0.996 [0.994, 0.997] | REFUSED | 0.173 |
| conjugate_wave | 0.007 [0.002, 0.014] | NOT REFUSED | 0.640 | 0.458 [0.435, 0.482] | PARTLY REFUSED | 0.339 |
| global_phase_rotation | 0.000 [0.000, 0.000] | NOT REFUSED | 1.000 | 0.004 [0.003, 0.005] | NOT REFUSED | 0.513 |

Mean max overlap of in-library probes: 0.512.

## 6. Study E: null, a pure phase wave stored (envelope off)

| sigma | acc ungated | acc gated | fraction assigned to phase 0 | refuse Haar | J cal | max neighbour overlap |
|---|---|---|---|---|---|---|
| 0.00 | 0.250 [0.250, 0.250] | 0.250 [0.250, 0.250] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 | 1.000 |
| 0.05 | 0.250 [0.247, 0.253] | 0.250 [0.247, 0.253] | 0.882 [0.876, 0.887] | 1.000 [1.000, 1.000] | 1.000 | 1.000 |
| 0.15 | 0.251 [0.247, 0.255] | 0.250 [0.246, 0.254] | 0.781 [0.774, 0.788] | 0.998 [0.997, 0.999] | 0.999 | 1.000 |

The four stored snapshots differ only by a global phase, so every stored pattern gives the same |overlap| up to floating-point rounding. Which phase wins is then decided by rounding and by the tie rule (lowest index), and the phase-0 column can differ across machines (one smoke replicate gave 0.71 on the development machine and 0.98 on a GitHub-hosted runner, for every Python version tried on each); the sigma 0.00 tau in study A is tie-dependent in the same way. It does not mean the memory recognises anything. The gate still works as an accept/refuse test of wave-likeness.

## 7. Study F: robustness map of the frozen gate

Rows: calibration sigma (tau is frozen there). Columns: in-library acceptance at the evaluation sigma.

| calibrated at | tau | J cal | refuse Haar | accept @0.00 | @0.05 | @0.15 | @0.30 | @0.45 | @0.60 |
|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.569 | 1.000 | 1.000 | 1.000 | 1.000 | 0.188 | 0.000 | 0.000 | 0.000 |
| 0.15 | 0.331 | 0.998 | 0.996 | 1.000 | 1.000 | 0.997 | 0.335 | 0.079 | 0.029 |
| 0.30 | 0.228 | 0.722 | 0.870 | 1.000 | 1.000 | 1.000 | 0.821 | 0.486 | 0.323 |

Tau by matched calibration sigma (study A): 0.00: 0.658, 0.05: 0.569, 0.10: 0.428, 0.15: 0.331, 0.20: 0.276, 0.30: 0.228, 0.45: 0.201, 0.60: 0.189.

## 8. Study G: does the phase structure matter?

| sigma | complex projection | magnitude-only classifier | difference |
|---|---|---|---|
| 0.00 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| 0.05 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] |
| 0.10 | 1.000 [1.000, 1.000] | 0.996 [0.995, 0.997] | 0.004 [0.003, 0.005] |
| 0.15 | 1.000 [0.999, 1.000] | 0.817 [0.803, 0.830] | 0.183 [0.169, 0.196] |
| 0.20 | 0.992 [0.991, 0.994] | 0.589 [0.572, 0.606] | 0.404 [0.387, 0.421] |
| 0.30 | 0.901 [0.896, 0.905] | 0.393 [0.384, 0.403] | 0.507 [0.497, 0.517] |
| 0.45 | 0.694 [0.688, 0.701] | 0.313 [0.308, 0.319] | 0.381 [0.372, 0.389] |
| 0.60 | 0.545 [0.539, 0.552] | 0.282 [0.278, 0.287] | 0.263 [0.255, 0.270] |

## 9. Interpretation (hand-written)

All statements are about this SYNTHETIC toy and its seeded probes. They
are not about hearts, patients or any clinical quantity, and no rate here
is the accuracy of a clinical test. Numbers are from the confirmation set
and are checked against `docs/results/confirm.json` by a test.

### What the pre-registered results do show

- Recognition: with the envelope in place the memory names the stored
  phase of a noisy probe essentially always up to sigma 0.15 (mean
  accuracy 0.9995, H1), 0.901 at sigma 0.30, and 0.545 at sigma 0.60
  against a chance level of 0.25. The supplied single-seed "39/40" was
  not a lucky draw: the gate, not the memory, rejects the occasional
  probe (gated accuracy 0.996 at sigma 0.15).
- Refusal of random fields: the gate refuses Haar-random fields 0.996 of
  the time at sigma 0.15 (H2) and separates in-library from
  scrambled-phase fields with AUC 0.99998 (H5). Refusal gets worse as
  noise grows because the two score distributions overlap: at sigma 0.30
  the calibrated gate refuses 0.870 of Haar fields while accepting only
  0.821 of in-library probes.
- Controls behave: label-shuffled recognition sits at chance, 0.2464
  [0.2405, 0.2522] (H3), and a pure phase wave is recognised at chance,
  0.2505 (H4; ablation `envelope_off` confirms a 0.65 to 0.75 drop at sigma 0.30 and 0.15).

### What the results show about limits (read these as findings)

- The gate is blind to a global phase rotation of a stored wave (H8) and
  accepts a wave sitting between two stored phases (H9). With noise-free
  probes of the deformed kinds, nothing is refused except random-like
  kinds: time-shifted waves 0.000, half-masked waves 0.000 to 0.024,
  conjugate (reversed-phase) waves 0.007, magnitude-permuted waves 0.047,
  scrambled phases on the stored envelope 0.721 (PARTLY REFUSED).
- Part of that is a confound that the first multi-seed run exposed, so a
  noise-matched control was added (amendment A1): noise-free deformed
  waves out-score noisy in-library probes. With the same sigma 0.15 noise
  on both, those kinds become PARTLY REFUSED (time-shifted 0.31,
  conjugate 0.46, magnitude-permuted 0.73, scrambled phases on the
  envelope 0.89). So the gate is a partial, noise-sensitive separator for
  structured deformations; it is a reliable separator only for
  random-like fields.
- Because the noise-free AUCs for deformed kinds are far below 0.5
  (for example 0.076 for a time-shifted wave), H6, which asks whether the
  max-overlap gate beats the `wave_scan` gate there, is satisfied only in
  the sense that 0.076 exceeds 0.000. Neither gate separates those probes.
  With noise matched, max-overlap reaches AUC 0.873 on the time-shifted
  kind while `wave_scan` stays at 0.497, because `wave_scan` correctly
  treats a wave at any phase as a wave; it is a different question
  ("is this a wave?" versus "is this one of the stored phases?").
- On random and scrambled-phase fields the max-overlap gate is not better
  than the simple `wave_scan` gate (both AUC 1.000); it is far better than
  the phase-blind magnitude-profile gate there (0.709), and worse than it
  on magnitude-permuted fields noise-free (0.623 against 0.985), as
  expected for a gate that sees only magnitudes.
- The tau rule matters very little. The midpoint rule beats first-best by
  0.0022 in balanced accuracy against Haar fields (95% interval 0.0013 to
  0.0031; supported statistically in H7, tiny in size); the other rules
  agree with the midpoint rule to within 0.0001.
- A tau frozen at one noise level does not transfer: calibrated at sigma
  0.05 the gate accepts only 0.188 of in-library probes at sigma 0.15;
  calibrated at 0.15 it accepts 0.335 at sigma 0.30.

### Ablations (exploratory)

- The envelope is required: removing it drops recognition by 0.65 at
  sigma 0.30. A very wide envelope (width 64) behaves like a pure phase
  wave (0.298 at sigma 0.30).
- Narrower envelopes (width 4) are 0.021 more accurate than the default at
  sigma 0.30, because snapshots then light up different neurons; that is
  closer to a lookup of which neurons are bright than to phase storage.
  Wider envelopes (12) lose 0.072.
- More stored phases are harder: 8 phases give 0.951 at sigma 0.15 and
  0.753 at sigma 0.30. The supplied note that more snapshots would "blur
  and teach nothing new" is partly right: they overlap more (largest neighbour
  overlap 0.91 at 8 phases against 0.49 at 4) and lose accuracy under
  noise, but they stay well above chance.
- Network size matters through noise, not size: at the same absolute
  sigma, n = 128 changes accuracy by -0.003 (not distinguishable from 0);
  with sigma scaled to hold the per-neuron signal-to-noise ratio, n = 128
  gains 0.082 and n = 32 loses 0.170 at nominal sigma 0.30.
- Neighbour count k and pacemaker position move accuracy by about 0.01 or
  less at sigma 0.30. Several of these differences have Holm p below 0.05,
  but at that size they are not practically meaningful.

### Does the phase structure matter?

Yes, for this toy: a magnitude-only classifier is within 0.005 of complex
projection up to sigma 0.10, but at sigma 0.15 it reaches 0.817 against 0.9995 and at
sigma 0.30 it reaches 0.393 against 0.901 (difference 0.507). Under noise
the phase information is what keeps the stored snapshots apart.

### Limitations

- Everything is a seeded toy: a parametric curve, a phase wave with an
  invented envelope, absolute-sigma complex Gaussian noise, and
  hand-designed out-of-library fields. Other noise models, other probe
  kinds or another gate would give other numbers.
- Replicates share the same 64-neuron design and the same probe
  generators; the intervals describe variation over layouts and noise
  draws, not over model choices. Wilson intervals treat trials as
  independent and are optimistic.
- The 0.90 refusal classes and thresholds are reporting choices. The
  development set was looked at before the confirmation run, and
  amendments A1 to A3 in `docs/PROTOCOL.md` were made after that.
- The pure-phase null depends on floating-point tie behaviour, and the
  fraction assigned to phase 0 is not a recognition result.
- Nothing here transfers to real physiology. No term in the model
  corresponds to any biological quantity, and the toy was never compared
  with recorded data.
