# §13 record (applied mechanically by scripts/apply_section13.py)

* Inputs: `/srv/ss_step6_prep/step7_prep/PLACEHOLDER_test/step5/checks.json` (SHA-256 `36e197b7f089ce43bde219af38ad6c8124c81e19b7e99257437c1bee822798d5`), `/srv/ss_step6_prep/step7_prep/PLACEHOLDER_test/step5/gsite_record.json` (SHA-256 `26a538012bce89538141d29e9c944b54e79e6ddd8532c8a31167aea62314522a`).
* Generator SHA-256: `baf91b40b577de2d30efce03a49c4f45a5dbc5c22b57be3559423fff094b44bd`.
* Effect on §14 step 6: none (§13 governs interpretation and claims; the §14 step-6 computation (cells, arms, replicates, learners) is fixed by §10 and the code-lock projection record).

## Rules evaluated before the causal grid

| §13 condition | scope | locked fields | triggered | consequence when triggered |
|---|---|---|---|---|
| E1 fails (standardized, 278-case set) | FM-P / FM-P−C | `P.E1_278.pass` = True | **no** | "site-like information in representations" is not established for this dataset. FM-vs-FM−C comparisons are reported descriptively only. |
| E3-site fails on the 278-case set | FM-P / FM-P−C | `P.E3_site_278.pass` = True | **no** | the removal manipulation failed; FM−C arms are not interpreted. |
| E1 and E3-site pass on the 278-case set but fail on the 158-case set | FM-P / FM-P−C | `P.E1_278.pass` = True; `P.E3_site_278.pass` = True; `P.E1_primary.pass` = True; `P.E3_site_primary.pass` = True | **no** | FM vs FM−C comparisons in the causal grid are reported descriptively only, and P1b-FM / P2-FM are not tested. |
| E3-site passes but the MLP probe exceeds the margin | FM-P / FM-P−C, 278-case set | `P.E3_site_278.pass` = True; `P.E3_site_278.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | FM-P / FM-P−C, 278-case set | `P.E3_site_278.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-site passes but the MLP probe exceeds the margin | FM-P / FM-P−C, 158-case set | `P.E3_site_primary.pass` = True; `P.E3_site_primary.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | FM-P / FM-P−C, 158-case set | `P.E3_site_primary.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-state-retention fails (state destroyed) | FM-P / FM-P−C | `P.E3_state_primary.applicable` = False; `P.E3_state_primary.pass_` = None | **no** | FM−C differences are not attributed to site removal alone, and FM−C causal arms are not interpreted. |
| E3-state-retention not applicable (E2 primary fails) | FM-P / FM-P−C | `P.E3_state_primary.applicable` = False | **yes** | the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3). |
| E1 fails (standardized, 278-case set) | FM-S / FM-S−C | `S.E1_278.pass` = True | **no** | "site-like information in representations" is not established for this dataset. FM-vs-FM−C comparisons are reported descriptively only. |
| E3-site fails on the 278-case set | FM-S / FM-S−C | `S.E3_site_278.pass` = True | **no** | the removal manipulation failed; FM−C arms are not interpreted. |
| E1 and E3-site pass on the 278-case set but fail on the 158-case set | FM-S / FM-S−C | `S.E1_278.pass` = True; `S.E3_site_278.pass` = True; `S.E1_primary.pass` = True; `S.E3_site_primary.pass` = True | **no** | FM vs FM−C comparisons in the causal grid are reported descriptively only, and P1b-FM / P2-FM are not tested. |
| E3-site passes but the MLP probe exceeds the margin | FM-S / FM-S−C, 278-case set | `S.E3_site_278.pass` = True; `S.E3_site_278.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | FM-S / FM-S−C, 278-case set | `S.E3_site_278.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-site passes but the MLP probe exceeds the margin | FM-S / FM-S−C, 158-case set | `S.E3_site_primary.pass` = True; `S.E3_site_primary.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | FM-S / FM-S−C, 158-case set | `S.E3_site_primary.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-state-retention fails (state destroyed) | FM-S / FM-S−C | `S.E3_state_primary.applicable` = False; `S.E3_state_primary.pass_` = None | **no** | FM−C differences are not attributed to site removal alone, and FM−C causal arms are not interpreted. |
| E3-state-retention not applicable (E2 primary fails) | FM-S / FM-S−C | `S.E3_state_primary.applicable` = False | **yes** | the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3). |
| E1 fails (standardized, 278-case set) | REF / REF−C | `REF.E1_278.pass` = True | **no** | "site-like information in representations" is not established for this dataset. FM-vs-FM−C comparisons are reported descriptively only. |
| E3-site fails on the 278-case set | REF / REF−C | `REF.E3_site_278.pass` = True | **no** | the removal manipulation failed; FM−C arms are not interpreted. |
| E1 and E3-site pass on the 278-case set but fail on the 158-case set | REF / REF−C | `REF.E1_278.pass` = True; `REF.E3_site_278.pass` = True; `REF.E1_primary.pass` = True; `REF.E3_site_primary.pass` = True | **no** | FM vs FM−C comparisons in the causal grid are reported descriptively only, and P1b-FM / P2-FM are not tested. |
| E3-site passes but the MLP probe exceeds the margin | REF / REF−C, 278-case set | `REF.E3_site_278.pass` = True; `REF.E3_site_278.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | REF / REF−C, 278-case set | `REF.E3_site_278.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-site passes but the MLP probe exceeds the margin | REF / REF−C, 158-case set | `REF.E3_site_primary.pass` = True; `REF.E3_site_primary.mlp_exceeds_margin` = False | **no** | the claim ceiling is "linear site information removed; nonlinear site information remains". |
| E3-site passes | REF / REF−C, 158-case set | `REF.E3_site_primary.pass` = True | **yes** | the wording is "no longer exceeds the prespecified linear site-encoding boundary", never "equivalent to chance" or "eliminated". |
| E3-state-retention fails (state destroyed) | REF / REF−C | `REF.E3_state_primary.applicable` = False; `REF.E3_state_primary.pass_` = None | **no** | FM−C differences are not attributed to site removal alone, and FM−C causal arms are not interpreted. |
| E3-state-retention not applicable (E2 primary fails) | REF / REF−C | `REF.E3_state_primary.applicable` = False | **yes** | the report states that retention of state information could not be assessed. FM−C interpretation then rests on E3-site alone (§5.3). |
| E2 fails | FM-P / FM-P−C | `P.E2_primary.pass` = False | **yes** | "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery. |
| E2 fails | FM-P-nat | `P-nat.E2_primary.pass` = False | **yes** | "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery. |
| E2 fails | FM-S / FM-S−C | `S.E2_primary.pass` = False | **yes** | "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery. |
| E2 fails | REF / REF−C | `REF.E2_primary.pass` = False | **yes** | "video representations recover the confounding state" is not established. FM-vs-NV comparisons cannot be read as confounder recovery. |
| G-SITE fails | design (code lock) | `gsite.gate_pass_primary` = True | **no** | C is not instrument-like in the constructed design at K = 1, P = 0. P2-SITE and P2-ORACLE become P3, and no amplification claim is made. |

## Family conditions (§12.2) for §14 step 7

* P1b-FM / P2-FM conditions from the locked `fm_conditions_primary` (key P): E1 = True, E3-site = True, E3-state = True; G-SITE (code lock) = True.
* Families tested at step 7: P1b-FM = yes, P2-FM = yes, P2-SITE = yes, P2-ORACLE = yes, P1a = yes, P1b-SITE = yes.
* `grid_conditions.json` holds these conditions as the locked grid driver's `--conditions` input.

## Deferred to §14 step 7 (need the family verdicts)

* E1 and E3 (both components, §5.3) pass but P1b-FM and P2-FM are INCONCLUSIVE (needs the family verdicts, §12.3)
* Family verdicts: stated as consistent / inconsistent with the theory-motivated direction (§12)

## Standing rules (no step-5 condition)

* Representation wording ("video-derived representations", arm-specific wording of §1)
* Native arm differs from standardized: attributed to acquisition shortcuts, not to image content
* REF arm: not a fair model comparison, not a pixel-level replication of K4, may retain frame-rate-derived information
* FULL arm: an exchangeability oracle / implementation sanity reference; its finite-sample bias is reported
* All claims describe a deliberately constructed orthogonal benchmark (§1, §7.2)
