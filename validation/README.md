# Reference validation workflow

The user selected **DrikGanita** as the calendar reference. The supplied family section is implemented; teacher review remains pending; see `WORDING_REVIEW.md` for the separate wording and pronunciation review.

The original three hand-recorded day boards are preserved as `drikganita-*.json`. Bulk captures use the same site's public read-only calculation request, with explicit Kannada/Amanta/Drik, centre sunrise, zero altitude, city coordinates and timezone. A separate first-party source engine claim is recorded in `reference/source-profile.json`; it is not an audit of the provider.

## Reproduce

Run from the project directory with its Python environment:

```bash
python -m tools.collect_reference --plan-only
python -m tools.collect_reference --workers 2
python -m tools.validate_reference --split development
python -m tools.report_reference
```

The predeclared plan covers 2026 for Bellevue, Bengaluru and Sydney, plus selected regular-Chaitra, Adhika-Chaitra, skipped-Pratipada and repeated-Pratipada cases. Source capture is slow: the endpoint also calculates information not needed for this comparison. Each response is cached, so interrupted collection can resume. Requests start at most once per second, with bounded workers. HTTP 401, 403 and 429 stop new collection; they are not bypassed. Three consecutive request failures also stop collection. After an upstream outage, `python -m tools.collect_reference --probe --workers 1` tries one uncaptured case once, with a 45-second timeout, before resuming the normal collector.

`--allow-partial` permits an explicitly incomplete development report while collection continues. It never opens reserved answers. `capture-status.json` describes the most recently completed collector run; count the saved city/date files for in-progress coverage.

Once the complete development report has no failed compared fields and its calculation/comparison code is frozen, release the reserved answers once:

```bash
python -m tools.validate_reference --split holdout --release-holdout
python -m tools.report_reference
```

The release saves calculation, comparator and plan hashes. It cannot be repeated as another unseen test. An explicitly named `--replay-holdout` is permitted only with unchanged hashes and writes a separate regression replay report. It never overwrites the first final comparison. If results are used to tune code, obtain new external test dates before claiming another unseen evaluation.

## Interpretation

- Capture identity is checked against city/date/profile and effective Drik calculation mode.
- Exact response bytes, a SHA-256 hash, parsed facts, request parameters and UTC capture time remain in each compressed JSON file.
- Tithi/Nakshatra/Yoga/Karana are checked at sunrise, noon and 18:00 using the source's active intervals. Month and Adhika are checked when the source interval covers the instant.
- Samvatsara, Ritu and Ayana are compared at sunrise. The source's at-time section does not supply these labels independently at noon/evening, so those checks are marked unavailable.
- Labels within 60 seconds of source transitions are uncertain, never passed. The precise JD timing differences are reported separately under a stated 60-second reference-agreement target.
- Transliteration aliases normalize equivalent names. They do not turn a different month, season, year or Paksha into a match.
- No missing or uncertain value counts as a successful check. No app-generated result is promoted into a reference answer.
- These comparisons concern the specified city-centre profile, not all Smartha families, all locations, every year 1900–2100, wording, or pronunciation.

See `reports/SUMMARY.md` and its JSON reports for completed coverage, mismatches, unavailable fields and timing differences. Preserve reported differences rather than silently changing numeric output to fit the source.

## Current collection interruption

On October 29, 2026 the upstream request repeatedly timed out. A later single-request recovery probe also timed out after 45 seconds. There are 790 saved cases out of 1,127 (337 missing). The offline development comparison covers 644 of 917 planned cases, with zero failed fields, 34 uncertain checks and 3,916 unavailable checks. The 210-case final set has not been released or evaluated. Resume cached collection when the provider recovers; this partial result does not establish full-year accuracy.
