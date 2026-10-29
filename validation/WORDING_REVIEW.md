# Wording and pronunciation review status

Calendar reference selected by the user: DrikGanita, Kannada/Amanta profile.

- Family section received: Kannada screenshot supplied October 29, 2026. Its fixed prose is transcribed in `sankalpa_display/family_wording.py`; the pictured calendar values are replaced with computed values.
- User confirmed retaining the existing Yajurveda opening and morning/noon/evening closing, and using the supplied geography only for US locations. The **My family Sankalpa** default uses standard expanded wording in other countries.
- Kannada, Devanagari and Roman Sanskrit (IAST) renderings share the same text. Ashwayuja is the supplied recital synonym for Ashwina; the underlying month calculation is unchanged. The supplied generic Shubha Nakshatra/Yoga/Karana phrase is preserved.
- User confirmation records the intended text and scope. Teacher review of grammar, ritual geography and the complete wording remains pending.
- Kshaya-month family wording: not provided. All available recital forms remain withheld when Kshaya is detected.
- Teacher review of audio pronunciation: pending. No family recording has been provided or approved.
- Expanded/family audio: the current public Vagdhenu adapter has a 100-syllable input guard. Calendar or text tests do not remove that limit or validate pronunciation.

Tests check script equivalence, changing calendar fields, month qualifiers, retained opening/closing and the audio limit. They cannot establish ritual approval. Record teacher approval and the specific recording reviewed only when that evidence is provided.

Calendar-only audio now contains the eight changing phrases specified by the user. The October 29 Chaturthi example passes the local length guard; full family text stays excluded. Teacher review of this generated passage is still pending.

Live calendar-only generation on October 29 was attempted once and rejected by the provider because the shared ZeroGPU quota was insufficient (180 seconds requested, 162 remaining). No calendar-only recording was produced or pronunciation-approved. No retry or quota bypass was attempted.

A subsequent user-authorized authenticated request succeeded on October 29: calendar-only audio was generated as a 13.11-second mono WAV at 24 kHz. Browser playback reached the end with no media error. The credential was supplied only through the running server environment, not saved in project files. Playback verification does not establish pronunciation accuracy; teacher review remains pending.
