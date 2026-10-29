# Calendar accuracy: implemented fixes and reference comparisons

Status: **identified defects corrected; external validation remains limited**. The original two website observations below are preserved as before-fix evidence. The implementation now replays their saved reference values in regression tests, plus a June 20 check captured after the fixes. This is not a certification of a full calendar year or of family ritual wording.

## Implemented profile and results

- Lahiri sidereal longitudes, Swiss Ephemeris/Moshier; timezone-aware city coordinates.
- True conjunctions solved numerically; Amanta intervals use [new moon, next new moon). Zero/one/two sidereal solar ingresses classify Adhika/ordinary/Kshaya; the regular month after Adhika is labelled Nija. Qualifiers appear in Sanskrit, Kannada and English transliteration.
- Default Hindu rising: geometric solar centre, without refraction, using Swiss Ephemeris BIT_HINDU_RISING. Apparent upper-limb rising remains an explicit alternative.
- Default solar Ritu: sidereal Mesha/Vrishabha = Vasanta and subsequent sign pairs; lunar Chaitra/Vaishakha pairing remains selectable. Agreement on three dates does not establish DrikGanita's entire Ritu algorithm.
- Default year turnover: exact regular-Chaitra conjunction. The optional sunrise-year convention waits for the first following sunrise; neither may precede the conjunction. Adhika Chaitra never advances the year. The earlier skipped-Pratipada festival-date fallback was removed after a real source mismatch; see the expanded investigation below.
- Ayana: sidereal Makara/Karka (not tropical solstice); supported API years 1900–2100. Country does not silently change the chosen conventions.
- Kshaya is detected with an omitted-month field and review flag; expanded/custom text and associated audio are withheld. The rare combined-month recital is deliberately not guessed. Short form and calendar remain available.

`validation/after-fixes.json` contains rerun values and time differences. All three recorded dates match all recorded normalized categorical fields and Adhika status. All fifteen recorded times differ by less than 60 seconds from the source's displayed minute. Hindu sunrise is 07:52:24 on October 28 and 05:26:14 on May 25; May now reads Adhika Jyeshtha / Vasanta.

A further live check for Bellevue on June 20, 2026 matches Jyeshtha / Grishma, Shukla Saptami, Purva Phalguni, Siddhi, Garaja and all five recorded times. Its board omits a Nija qualifier; the app derives Nija from the preceding Adhika month. The new fixture explicitly records the tithi end on June 21 to avoid comparing times across the wrong date.

The initial 23 automated tests also cover new-moon/tithi wrap boundaries, 2029 Adhika Chaitra versus regular Chaitra, 1983 omitted Magha, selectable convention isolation, all catalogue cities' sunrise weekdays, DST, three scripts and audio regressions. The 2026 interval sweep covers 2,190 sunrise/noon/evening instants across Bellevue and Bengaluru; it tests internal consistency, not independent reference agreement.

Boundary references: [2029 Ugadi](https://www.drikpanchang.com/telugu/festivals/ugadi/ugadi-newyear-date.html?year=2029) lists April 14 in India; [1983 historical calendar](https://www.mypanchang.com/historycalformat.php?cityname=IST&mn=2&yr=1983) identifies Kshaya Magha and Adhika Phalguna. See [traditional Soura and Chandra Ritu explanations](https://sanskritdocuments.org/sites/prkannan/Balabodha%20Sangraham%20-%202.pdf). These references inform specific cases, not every regional recital convention.

## Original comparison profile (before fixes)

- Bellevue: latitude 47.6101, longitude -122.2015, America/Los_Angeles.
- DrikGanita regional calendar: Kannada. Its Kannada documentation describes Amanta reckoning and Lahiri ayanamsa.
- Compare sunrise/day-board labels separately from the labels active at a specified current instant.
- Record sunrise definition explicitly. The app currently uses the apparent upper solar limb with refraction, through Swiss Ephemeris defaults.
- A candidate DrikGanita-compatible sunrise definition is Swiss Ephemeris Hindu rising: geometric solar centre, no refraction, geocentric position with solar ecliptic latitude ignored. The observations below are consistent with that definition; the website's exact internal implementation is not established.
- Ritu and Samvatsara turnover require explicit convention choices. Do not automatically classify every difference as numerical error.

Sources:
- https://drikganita.com/cities/bengaluru/kannada-panchanga
- https://drikganita.com/sankalpam
- https://www.astro.com/swisseph/swephprg.htm (section 8.12.1)

## Recorded observations

The source was read in a live browser using its city selector and date picker. Historical navigation initially displayed the previous date's data while loading; values were recorded only after the chosen date's board finished updating. Search-engine/cache previews were not used as current-day evidence.

Reference URLs and normalized facts, app results, coordinates, and diagnostic sunrise calculations are in `validation/drikganita-2026-10-28-bellevue.json` and `validation/drikganita-2026-05-25-bellevue.json`.

### Bellevue, October 28, 2026

App sample: 08:00 PDT, after both sunrise definitions and before the listed transitions. All reference times are local.

| Field | DrikGanita | App | Assessment |
|---|---|---|---|
| Month/year | Ashwina / Parabhava | Ashwina / Parabhava | Labels agree on this date |
| Ayana/Ritu | Dakshinayana / Sharad | Dakshinayana / Sharad | Labels agree on this date |
| Tithi | Tritiya → Chaturthi at 12:37 | Tritiya → Chaturthi at 12:37:13 | Within displayed minute |
| Nakshatra | Rohini → Mrigashira at 22:41 | Rohini → Mrigashira at 22:41:44 | Under one minute apart |
| Yoga | Variyana → Parigha at 15:10 | Variyana → Parigha at 15:10:37 | Under one minute apart |
| Karana | Vishti → Bava at 12:37 | Vishti → Bava at 12:37:13 | Within displayed minute |
| Sunrise | 07:52 | 07:46:52 | Different sunrise definitions need resolution |

A separate Hindu-rise diagnostic gives **07:52:24**, consistent with DrikGanita's minute-level display. This is not the app's current configured sunrise. The default sunrise and Hindu sunrise differ by about 5 minutes 32 seconds here; treating that as an ephemeris error would be premature.

At late evening the day board still lists the earlier tithi/nakshatra and their transition times. The app's current-moment Chaturthi/Mrigashira must be compared with the interval active at that moment, rather than the board's first label.

### Bellevue, May 25, 2026

App sample: 06:00 PDT, after both sunrise definitions and before the listed transitions.

| Field | DrikGanita | App | Assessment |
|---|---|---|---|
| Month | Adhika Jyeshtha | Jyeshtha, no Adhika flag | Missing leap-month distinction |
| Samvatsara | Parabhava | Parabhava | Label agrees on this date |
| Ayana | Uttarayana | Uttarayana | Label agrees on this date |
| Ritu | Vasanta | Grishma | Convention/rule mismatch; unresolved |
| Tithi end | Dashami at 16:41 | Dashami at 16:41:25 | Under one minute apart |
| Nakshatra end | Uttara Phalguni at 15:38 | Uttara Phalguni at 15:38:58 | Under one minute apart |
| Yoga end | Vajra at 14:45 | Vajra at 14:45:27 | Under one minute apart |
| Karana end | Gara at 16:41 | Garaja at 16:41:25 | Normalized name; under one minute apart |
| Sunrise | 05:26 | 05:20:05 | Different definition; see diagnostic in fixture |

The app simply maps Ritu from the lunar month name. One Vasanta/Grishma disagreement does not establish DrikGanita's full Ritu algorithm; obtain that rule before changing ours.

## Proposed acceptance criteria

These are this project's engineering criteria, not a published accuracy guarantee from DrikGanita.

1. **Fixed conventions:** record region, lunar-month system, ayanamsa, coordinates, timezone, sunrise definition, year turnover, and Ritu/Ayana rules for every comparison.
2. **Categorical agreement:** require exact normalized agreement on Samvatsara, month, Adhika/Nija/Kshaya status, Paksha, Vara, and the active Tithi/Nakshatra/Yoga/Karana away from transition uncertainty windows. Any unresolved mismatch is a failure for that profile.
3. **Time agreement:** target differences of at most 60 seconds for minute-resolution reference transition times and sunrise, only after the definitions agree. Retain seconds internally. If the source exposes precise seconds, use those and reconsider the tolerance. This measures agreement with that reference, not absolute observational accuracy.
4. **Boundary checks:** test before and after every new moon, lunar-new-year turnover, leap-month start/end, solar ingress, sunrise, and DST change. Around rounded source times, treat the reference minute as uncertain rather than guessing an exact second.
5. **Coverage before a validation claim:** compare every day at sunrise/noon/evening for an agreed full calendar year including an Adhika month (2026), plus documented Kshaya examples and a second independent reference for disagreements. Start with Bellevue; claims about other cities require their own location tests.
6. **Provenance:** save reference date, values, URL, precision, capture date and settings. Do not count different pages backed by the same source as independent confirmation without checking provenance.
7. **Report limits honestly:** report matched fields, time-error ranges, failed cases and untested dates. A pass on two dates is not “100% accurate”. Wording and audio pronunciation require separate family/teacher review.

## Remaining work before a broad validation claim

- Expand independently sourced fixtures to every day in a leap-month year and multiple locations; retain unseen dates for a final comparison.
- Check every year-turnover case, including Pratipada skipped/repeated at sunrise, against the family's chosen local Panchanga.
- Resolve any remaining Ritu/Ayana differences by convention rather than changing numerical output just to match labels.
- Obtain the family's Kshaya-month recital convention and teacher review of the full wording and audio pronunciation.

The reference site's current homepage footer names Skyfield/JPL DE440s, while some indexed older pages name Swiss Ephemeris. Record the observed version/engine claims rather than assuming engine independence. This investigation establishes a comparison target, not an audited certification of either implementation.

## Expanded investigation (October 29, 2026)

The user selected DrikGanita as the calendar reference and supplied the family middle section in Kannada; existing opening/session closing and US-only geography were confirmed. The reproducible workflow is in `validation/README.md`; current coverage and failures are in `validation/reports/SUMMARY.md`. It predeclares every 2026 date for Bellevue, Bengaluru and Sydney plus selected year boundaries, with 210 source cases reserved from development evaluation.

The public daily response exposes precise Julian-day events and active intervals, so it supports more checks than the original minute-only day-board records. The comparison retains an explicit 60-second engineering tolerance and reports the actual precise timestamp differences. A near-transition label is uncertain, not a pass; a missing source field is unavailable, not a pass. Samvatsara/Ritu/Ayana metadata is at sunrise and is not silently promoted into independently observed noon/evening labels.

### Year-boundary defect found and corrected

DrikGanita's Bengaluru development cases show:

- April 10, 2032 sunrise: Amavasya, Phalguna, Virodhikrit.
- April 11, 2032 sunrise: Dvitiya, Chaitra, Paridhavi. Pratipada touches no sunrise.
- March 17 and 18, 2037 sunrises: Pratipada, Chaitra, Pingala on both days (a repeated-Pratipada case).

The app formerly used a civil Ugadi skipped-Pratipada fallback to change Samvatsara on the conjunction date’s sunrise. In 2032 that sunrise precedes the conjunction, so it produced Paridhavi too early. The fallback was removed. Default turnover is now the actual regular-Chaitra conjunction; the optional day-based mode waits for the first sunrise after it. A festival observance date is not used as a substitute for an astronomical year boundary. Original source payloads and a compact evidence extract remain in `validation/reference/` and `validation/year-turnover-bengaluru.json`.

The broader comparison normalizes equivalent names such as Śarat/Sharad without changing the solar Ritu or Makara/Karka Ayana calculations. It records actual disagreements rather than treating every spelling difference as a new calendar convention.

No new broad validation claim is made while collection or reserved-set evaluation is incomplete. The supplied family section has been implemented; teacher wording review, Kshaya recital convention and teacher audio review remain pending. The software suite now contains 43 passing regression/provenance/accounting tests, which are distinct from external agreement results.

## Weekday display correction, October 29, 2026

The user supplied a DrikGanita date-board screenshot showing Thursday alongside Chaturthi (ends 9:40 AM), Mrigashira (ends 8:34 PM), Parigha and Balava. The app previously applied the previous sunrise’s weekday before dawn. Vara now follows the city’s local civil date, including in standard and family recital fields. A regression checks Wednesday 23:59:59, Thursday midnight, before/after sunrise, and equivalent UTC input. This screenshot establishes the selected date-board convention; it does not independently validate all pre-dawn ritual conventions. The previous sunrise date remains separate API metadata.
