# GitHub and Vercel

This repository is prepared for a GitHub-connected Vercel deployment. A hosted deployment has not been created or tested yet.

## Push to GitHub

Create an empty GitHub repository (do not initialize another README), then run from this project directory:

```bash
git remote add origin https://github.com/YOUR_USER/smartha-sankalpa-display.git
git push -u origin main
```

Replace `YOUR_USER` with your GitHub account. The local repository already has an initial commit on `main`.

## Connect Vercel

1. In Vercel, choose **Add New → Project**, import that GitHub repository and keep the root directory as the repository root.
2. Use the **FastAPI** framework preset. Leave build/install/output overrides at their defaults; this is a Python application, not a static HTML upload. The HTML page and `/api/*` routes deploy together.
3. Under **Environment Variables**, add `HF_TOKEN` with your Hugging Face token for each environment where audio should work. Add it in Vercel's settings; do not put the value in Git, HTML, a URL or a committed `.env` file. `VAGDHENU_SPACE` is optional; the default is the existing Vagdhenu demo.
4. Keep Fluid compute enabled. `vercel.json` selects a 300-second maximum request duration. The Python runtime is pinned to 3.12 by `.python-version`.
5. Deploy, then check the home page, `/api/locations` and `/api/panchanga?city=bellevue`. Confirm the date, city, script and highlighted Sankalpa fields. Generate calendar-only audio once and verify playback and WAV download.
6. Future pushes to the linked production branch deploy automatically; branch/PR previews follow your Vercel project's Git settings.

The astronomy dependency (`pyswisseph`) has no prebuilt CPython 3.12 Linux wheel in its current PyPI release and must compile from source during dependency installation. GitHub CI installs it and runs the tests on Ubuntu/Python 3.12 and 3.13. The first Vercel build must still verify its build environment; local tests do not certify that remote build.

Vercel docs: [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime](https://vercel.com/docs/functions/runtimes/python), [function limits](https://vercel.com/docs/functions/limitations).

## Hosted audio

Local operation retains the background worker and persistent local WAV cache. When Vercel sets `VERCEL=1`, audio generation instead completes within one request, uses temporary files and returns the WAV directly inside the response as a data URL. It does not rely on a follow-up request finding the same instance or a writable project directory. Files over 3 MB are rejected before encoding, keeping the JSON response below Vercel's 4.5 MB response limit.

The browser reuses up to eight hosted recordings during the current page session, shared across display scripts. Reloading clears this session cache; hosted recordings are not stored permanently. Download a WAV if you want to keep it. Slow providers can still exceed Vercel's request deadline, and Hugging Face quotas still apply. Use Vercel's access protection for a household-only deployment, since visitors able to call the audio endpoint can consume its Hugging Face quota.

## Open on the tablet

Open the deployment's HTTPS URL in the tablet's browser, select the city and script, then enable **Home display**. Settings and wording variations stay in that browser; laptop customizations do not automatically transfer. Internet is required for hosted calendar updates. The default supplied wording is included in the application. Configure the tablet's screen timeout/brightness as desired.

`localhost:9000` on the tablet refers to the tablet itself. Use the deployed HTTPS URL instead.
