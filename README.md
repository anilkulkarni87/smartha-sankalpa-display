# Smartha Yajurveda Sankalpa home display

A locally calculated Panchanga and editable Yajurveda Sandhyavandana reader. Bellevue is the default; country and city selectors cover 20 cities across seven countries. Each city uses its own coordinates, IANA timezone, sunrise and local calendar weekday. Location settings never mutate shared server globals.

## Run on port 9000

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

If your old server is still running, stop it with Ctrl+C in its terminal first. Restart after Python-file changes; refreshing a page alone does not reload the backend.

Open **http://localhost:9000/**. To use your existing command:

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 9000
```

For the Bellevue home view: **http://localhost:9000/?city=bellevue&display=1**. Query parameters override the saved city/display mode on every reload; use the plain URL to follow the browser's saved choices.

Another device on the same Wi-Fi can use `http://<server-LAN-IP>:9000/` when the backend binds to `0.0.0.0` and the firewall allows it. `localhost` on a tablet means the tablet itself. Port 6000 is browser-blocked; 9000 works normally.

## Everyday use

1. Select Country, then City. The clock and all calendar timestamps use the selected city's timezone, even when the browser is elsewhere.
2. Choose Morning, Noon or Evening manually. Selection changes the concluding Sankalpa action; it does not calculate the proper ritual performance window.
3. The reader offers English transliteration, Sanskrit (Devanagari), and Kannada directly in both normal and home-display views. Household settings offers font size, optional gotra, sunrise/current calendar mode, and an editable template.
4. Save household settings. Use **Edit wording** or **Add variation** beside the reader for wording changes; old custom text is preserved.
5. Choose **Home display** and optionally **Full screen**. Exit home display to change city/settings. The page refreshes calendar values every minute and when returning to the tab.

Settings are browser-local, including the city, session, font and script. Save them on the physical home-display device. Browsers treat different ports as separate storage origins; old settings on 8000 do not automatically transfer to 9000. Failed storage access does not stop the page, but settings then last only for the current page session. Failed calendar updates show a visible warning; changing city clears values from the old city immediately.

## Yajurveda wording

The reader defaults to **My family Sankalpa**, using the supplied Kannada section with the user-confirmed existing Yajurveda opening and morning/noon/evening closing. The ordinary selector contains only this wording and variations you save. The supplied geography applies to US cities; other countries retain neutral expanded geography until you save a local variation.

Choose **Edit wording** to update the selected wording, or **Add variation** to make a named copy. Edit in Kannada, Devanagari or Roman Sanskrit (IAST). The live reader previews unsaved edits; **Cancel** discards them. **Save wording** converts the text into all three scripts locally and saves it in this browser. A dropdown inserts daily calendar fields at the cursor, and placeholders remain intact. These are script conversions, not translations of meaning. The editor validates placeholders and keeps the draft if saving fails.

**Restore supplied wording in editor** retrieves the original, without changing the saved version until Save. Named variations apply to their creation country. **Hide this variation** removes a copy from the selector; **Restore hidden variation** in Household settings recovers it. Original supplied text and old custom-template storage are preserved. Browser settings and wordings do not automatically transfer to another device; backup/export remains future work.

Calendar fields and session endings update automatically. The supplied generic Shubha Nakshatra/Yoga/Karana phrase and Ashwayuja month name are retained. Gotra is included only if its placeholder is inserted. Adhika/Nija qualifiers are included; Kshaya still withholds recital until reviewed. Teacher review of the wording and pronunciation remains pending.

## Repository layout

```text
app.py                       # Local and Vercel entry point
sankalpa_display/             # API, calendar, wording and audio
  web/                       # index.html, app.js and styles.css
tests/                       # Automated regression checks
tools/                       # Reference capture and comparison commands
validation/                  # Source fixtures, plans and reports
docs/                        # Development, deployment and display guides
scripts/                     # Graphify wrapper
```

## Hosting and future development

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) to push this repository to GitHub, connect Vercel and open the display on a tablet. See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for local checks and the project-scoped Graphify workflow.

## Vagdhenu audio playback

1. Choose your city and calendar view. Open **Calendar text used for audio** to review the eight changing phrases: year, Ayana, Ritu, month, Paksha, Tithi, Vaara and Nakshatra.
2. Choose **Generate calendar audio · Vagdhenu**. Only that calendar passage, beginning with Sri, is normalized to Devanagari and sent to the [Vagdhenu Hugging Face Space](https://huggingface.co/spaces/prathoshap/vagdhenu-demo). The full family wording, gotra and fixed opening/closing are excluded. Nothing is sent automatically on page load or refresh.
3. Wait for **Audio ready**, then use **Play**. Speed, repeat and WAV download remain available. Audio is Sanskrit in every display script.
4. A change to any spoken calendar value clears the previous player. Switching display scripts clears the player but reuses the same canonical cached audio. Session selection and edits to fixed family wording do not change this calendar-only passage.

The adapter uses the published `/synthesize` API with the `gadya` prose reference and seed 60. It downloads the generated WAV into `.audio-cache/`, keyed by normalized Sanskrit text, provider, reference and seed. Equivalent default text in the three scripts reuses the same file. Cached playback works without the remote service and survives app restarts; new generation needs internet access. A queued job runs in a background worker so the calendar stays responsive. No browser speech synthesis substitute is used.

The hosted demo currently permits **one passage, up to 100 syllables, and 10 requests per network/IP per day**. Requests that exceed its input limits are rejected locally; the app does not split long Sankalpas to bypass those limits. Cached replays do not spend another request. GPU availability, authentication requirements and quotas can still affect generation, and errors are displayed explicitly. There is no automatic retry. The requested October 29 calendar-only passage passes the local limit at an estimated 53 syllables. Actual text is still checked on every request; longer future phrases can be rejected. The complete family text remains outside this audio feature. Supporting long audio requires a separate adapter/deployment change; selecting another Space alone does not remove the current input guard.

Optional server environment settings:

- `VAGDHENU_SPACE`: a Gradio Space ID or your own compatible Gradio deployment exposing `/synthesize` with `text`, `meter_choice`, `seed`, returning an audio filepath and status. Defaults to `prathoshap/vagdhenu-demo`.
- `HF_TOKEN`: optional Hugging Face token if your deployment/account needs it. Keep it in the server environment, never in HTML or a URL.

Restart the server after changing these settings. The standard installation includes `gradio_client` and `indic-transliteration`; it does not download the neural model weights. The [upstream local setup](https://github.com/prathoshap/vagdhenu#install--quickstart) requires Python 3.10 and an NVIDIA CUDA 12.1 GPU. For a Pi/Mac display, use remote generation and local cached playback. Add a speaker or use your display's audio output for the physical unit.

Generated speech is an AI pronunciation aid, not a certified Yajurveda chanting lesson. The prose reference does not establish your family's swara, pauses or pronunciation. Have a knowledgeable teacher review the result.

Named wordings store all three scripts together. Saving explicitly transliterates the edited Sanskrit text into the other scripts locally; it does not translate meaning. Old custom storage is retained and loaded as a named variation when possible. Restore the supplied text in the editor, then Save, to replace an edited family version.

## Calendar scope

- Swiss Ephemeris/Moshier calculation; Lahiri sidereal longitudes.
- Tithi, Nakshatra, Yoga and Karana from solar/lunar longitudes, with next-transition timestamps.
- Exact sunrise instant retained so sunrise mode doesn't incorrectly select the previous weekday.
- Current moment is the default; sunrise mode is informational and clearly labelled.
- Amanta months use bracketed true solar/lunar conjunctions and sidereal solar-ingress counts: zero = Adhika, one = ordinary (Nija after Adhika), two = Kshaya. The API reports exact month bounds, classification and omitted month. Kshaya ritual wording varies, so all available recital forms and their audio are withheld for review; the calendar remains available.
- Samvatsara turns over at the exact regular-Chaitra new moon by default, skipping Adhika Chaitra. The optional sunrise-year mode waits until the first sunrise after that conjunction, even if Pratipada touches no sunrise. Ugadi festival-date rules are not used to advance the year before the new moon. These are explicit conventions; confirm your family’s practice.
- Default Ritu uses sidereal solar-sign pairs (Mesha/Vrishabha = Vasanta); lunar Chaitra/Vaishakha pairing is selectable. Default sunrise is geometric Hindu rising; apparent upper-limb/refraction rising is selectable. Ayana follows sidereal Makara/Karka. Country selection does not change these calendar conventions or reverse Ayana in the Southern Hemisphere.
- Coordinates are approximate city centres, not a precise household location. Add cities in `locations.py` with an IANA timezone and latitude/longitude.
- Check against your trusted local Panchanga on ordinary dates, transition days, lunar new year and leap months before relying on this for recital. Tests verify software behavior, not independent ritual/astronomical correctness.

## API and checks

- `GET /api/locations` returns the offline city catalogue.
- `GET /api/panchanga?city=bengaluru` returns current values for that city.
- Optional `at=2026-10-28T12:00:00` is interpreted in the selected city's timezone. Include an offset to specify a shared instant across cities.
- Optional `sunrise_mode=hindu|apparent`, `ritu_mode=solar|lunar`, `year_mode=sunrise|conjunction` select conventions; responses record them. Household settings saves these choices in the browser. Dates outside 1900–2100 and invalid inputs return HTTP 422.

```bash
python -m pip install -r requirements-dev.txt
python -m unittest -v
```

The 43 tests include the three recorded DrikGanita comparisons, 2026 daily sunrise/noon/evening month-interval invariants for Bellevue and Bengaluru (2,190 instants), new-moon boundaries, Adhika/Nija script forms, the 2029 Adhika-Chaitra year boundary, and the historical 1983 Kshaya-Magha review flag. The year sweep is internal numerical coverage, not independent reference validation. Tests also cover all catalogue cities' sunrise boundaries, shared-instant consistency, city switching, northern/southern DST, validation, HTML loading outside the project directory, three-script phonetic equivalence, audio caching, changed-session keys, provider error handling, and WAV API serving. Audio tests use a temporary WAV stub; a separate live Vagdhenu request produced an 8.09-second morning recording and browser playback was verified. The updated UI was checked for country/city selection, noon wording, Kannada and settings persistence through reload.

## Home unit and licensing

See `docs/HOME_DISPLAY.md` for the recommended standalone arrangement and setup checklist. No hardware has been configured by this update.

Review Swiss Ephemeris/pyswisseph licensing before public hosting or redistribution. This remains a local prototype with unvalidated calendar edge cases.

## Accuracy investigation

See `docs/ACCURACY.md` for the named DrikGanita Kannada/Amanta Bellevue comparison profile, three recorded live reference dates, and proposed acceptance criteria. The data is in `validation/`. The identified sunrise, Adhika and Ritu mismatches are corrected under the default profile. The three recorded day-board comparisons pass within 60 seconds for all five recorded times per date. This limited comparison does not establish full-year accuracy. See the report for exact conventions and remaining validation work.

## Expanded DrikGanita validation

The user selected DrikGanita as the reference. `validation/README.md` documents the paced, resumable collection, exact response provenance, offline comparison and reserved final set. `validation/reports/SUMMARY.md` reports the actual completed coverage; an in-progress run must not be described as full-year validation.

A development comparison found a real skipped-Pratipada defect: Bengaluru on April 10, 2032 remains Amavasya / Virodhikrit at sunrise. The former festival-date fallback advanced the year too early. The code now uses regular-Chaitra conjunction by default, and the optional sunrise mode never precedes that conjunction. A dedicated regression covers this case; the source evidence is preserved in `validation/year-turnover-bengaluru.json`.

Existing saved calendar choices remain available. To use the chosen DrikGanita reference profile, select Hindu sunrise, solar Ritu and **Regular Chaitra: exact new moon** in Household settings, then Save. The supplied family section is available as **My family Sankalpa** in all three scripts, with computed calendar fields and the existing opening/session closing. Other countries retain the standard expanded wording. Teacher wording and pronunciation review remain pending; see `validation/WORDING_REVIEW.md`.

Weekday correction (October 29, 2026): Vara and both recital forms follow the selected city’s local civil date, changing at midnight, to match the user-supplied DrikGanita date board. Before sunrise on Thursday October 29, the display and recital now use Guruvara. Sunrise-day metadata remains separate; lunar fields retain their own astronomical transitions.

The recital highlights dynamic Samvatsara, Ayana, Ritu, month, Paksha, Tithi, Yoga and Karana in gold, Vaara in teal and Nakshatra in lavender in every script and saved variation. Highlighting preserves the underlying plain text used for audio and safely renders user wording as text. Printed colours use darker shades for a white page.

On Vercel, calendar audio returns within one request using temporary storage, and the page keeps a bounded session cache. Local operation retains its disk-backed cache and background worker. See docs/DEPLOYMENT.md for runtime limits and the required HF_TOKEN environment setting.
