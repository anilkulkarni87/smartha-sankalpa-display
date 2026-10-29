# DrikGanita reference validation

Generated UTC: 2026-10-29T15:58:04.743967+00:00

Reference: DrikGanita, Kannada / Amanta / Drik, geometric-centre sunrise, altitude zero, Smarta Ekadashi profile. City-centre coordinates and IANA timezones are fixed in the plan. This compares agreement with one named external source; it is not an independent certification of astronomical truth or ritual wording.

## Coverage

| Stage | Cases evaluated | Expected | Passed checks | Failed checks | Uncertain | Unavailable | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| development | 644 | 917 | 25674 | 0 | 34 | 3916 | incomplete |
| holdout | 0 | 210 | — | — | — | — | Not evaluated |

A case is one city/date, sampled at sunrise, local noon and 18:00. A check is one field at one sample, not one independently sourced observation. The base plan includes every date of 2026 for Bellevue, Bengaluru and Sydney (1,095 city/dates), plus 32 predeclared boundary cases.

| City | 2026 cases compared | Expected | Boundary cases compared |
|---|---:|---:|---:|
| bellevue | 281 | 365 | 8 |
| bengaluru | 167 | 365 | 16 |
| sydney | 164 | 365 | 8 |

## Timing and names

The acceptance threshold is 60 seconds of reference agreement. Source Julian-day timestamps expose finer precision than the website’s minute display; the actual worst differences below are reported rather than implied to be 60 seconds. This threshold is an engineering choice, not a claim about observational error.

| Stage | Largest absolute precise-timestamp difference |
|---|---:|
| development | 4.066 seconds |

Names are normalized through explicit transliteration aliases (for example, Gara/Garaja and Caturthi/Chaturthi). Different month, season, Paksha or year values are not merged just to make a comparison pass. Source event intervals select the active tithi/nakshatra/yoga/karana at noon and evening.

Comparisons within 60 seconds of a source transition are marked uncertain, never passed. When a source interval does not cover an instant, it is marked unavailable. The JSON reports retain all such cases and every failed check.

## Calendar boundaries and conventions

- Adhika Chaitra: 12 captured city/date cases compared.
- regular Chaitra after Adhika: 12 captured city/date cases compared.
- repeated-Pratipada candidate: 4 captured city/date cases compared.
- skipped-Pratipada candidate: 4 captured city/date cases compared.

The predeclared 2026 plan also includes ordinary lunar-year turnover, the skipped-Pratipada candidate at Bengaluru in March 2026, and the Adhika/Nija Jyeshtha boundaries. These are selected observed cases; no claim is made that every year between 1900 and 2100 has been externally checked.

The app keeps its stated solar Ritu and sidereal Makara/Karka Ayana conventions. Development found and corrected one genuine Samvatsara defect: a civil Ugadi fallback advanced the year before conjunction on Bengaluru April 10, 2032. Default turnover is now exact regular-Chaitra conjunction; the optional sunrise mode waits for the first following sunrise. The evidence extract and dedicated regression preserve this finding. Equivalent Śarat/Sharad spellings are normalized; different seasons are never merged.

## What this cannot establish

- DrikGanita supplies year, Ritu and Ayana as sunrise metadata; its at-time section does not expose those fields independently at noon/evening. Those checks are unavailable, not assumed to pass.
- The source identifies Adhika but does not separately certify our Nija or rare Kshaya classification through this response schema. Kshaya recital still requires explicit family guidance.
- City-centre comparison does not establish accuracy for a different household’s precise coordinates, elevation or horizon.
- The supplied family Sankalpa section is implemented for US cities, with the user-confirmed existing opening and session closing. Teacher review of wording and audio pronunciation remains pending. No AI-generated approval substitutes for that review.

## Reproduction and provenance

`validation/reference/plan.json` fixes locations, profiles, cases, deterministic split and calculation-code hashes before bulk capture. Exact source payloads, SHA-256 hashes, request parameters and capture timestamps are stored in compressed city/date files. Capture stops on HTTP 401, 403 or 429; cached facts can be replayed without network access.

The 210 reserved cases are excluded from development comparisons. `holdout-release.json` records the frozen calculation hashes when the reserved answers are first evaluated. After that they are a regression set and cannot honestly be described as unseen again. Changing calculation code after release requires new external holdout cases.

Files: `validation/reports/development.json`, `validation/reports/holdout.json` (when released), `validation/reference/capture-status.json`, and the compressed reference corpus.

## Recorded differences

No failures in the fields compared so far. Coverage and unavailable/uncertain counts above still limit the conclusion.
