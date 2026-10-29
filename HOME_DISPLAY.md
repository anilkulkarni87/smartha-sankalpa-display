# Building the everyday home unit

## Recommended arrangement

Use a Raspberry Pi 4 or 5 with a 7–10 inch touchscreen, a suitable official power supply, a microSD card, and a case/stand. A 10-inch landscape display gives more room for reading from a distance; compare actual text size before buying. A reused tablet is a useful first trial, although its backend must stay running on another machine.

Run both the Python app and Chromium on the Pi. This makes the finished display independent of your Mac. The browser opens the local page; it does not need a paid Panchanga API. Connect a speaker for Sankalpa playback. Generate audio through Vagdhenu when online; downloaded recordings are cached for subsequent playback. The Pi does not run the CUDA model itself. Once installed, calculations work locally, but the device clock must stay correct. Keep normal time synchronization working and check time after a power outage.

Raspberry Pi's [official kiosk tutorial](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/) explains booting directly into a full-screen Chromium page. Its [display documentation](https://www.raspberrypi.com/documentation/accessories/display.html) explains touchscreen connections. Use the instructions matching your Raspberry Pi OS version.

## First, trial the screen you already have

1. Run this project on the Mac at port 9000, bound to `0.0.0.0` if using another device.
2. On a tablet on the same Wi-Fi, open `http://<Mac-LAN-IP>:9000/`.
3. Choose your city, preferred script, and font size, then save.
4. Enable Home display and check the result from your normal reading distance. The compact view retains Samvatsara/Ayana/Ritu/Masa in a summary and shows Paksha/Tithi/Vara/Nakshatra prominently.
5. Select the session yourself before recitation. The selected session is remembered until you change it.

## Standalone Pi setup

1. Install Raspberry Pi OS with a graphical desktop, configure your screen, and confirm its time and network connection.
2. Copy this project folder to the Pi and follow the README installation commands there. Install the system's compiler/Python development packages if pip reports that building pyswisseph requires them.
3. Start `python run.py` and open `http://localhost:9000/` in Chromium on the Pi.
4. Configure city, language, template and font on the Pi's browser. Browser settings from your Mac won't transfer.
5. Configure a systemd service to start the app with the project's virtual-environment Python, a working directory pointing at this project, port 9000, an ordinary local user, and restart-on-failure. Test the service before kiosk startup.
6. Following the official kiosk tutorial, open a single page: `http://localhost:9000/?city=bellevue&display=1`. Replace the city ID if needed. Configure browser startup to wait until `http://localhost:9000/api/locations` responds successfully, so it doesn't open a connection-error page before the backend is ready.
7. Set display sleep/brightness through Raspberry Pi OS. The app itself does not prevent display sleep. Full screen can also be managed by Chromium kiosk mode.
8. Reboot and confirm the app opens without your Mac or a terminal remaining connected.

Service installation and kiosk boot configuration are device-specific and have not been applied or tested on a Pi in this update.

## Acceptance checks before everyday use

- Correct city and local time appear after boot and after a power outage.
- Country/city selection changes sunrise and timezone; switching back restores the correct city.
- Settings and font survive browser/Pi restart.
- Morning/noon/evening visibly change the Sankalpa ending.
- The day changes at local sunrise, and displayed transitions update without manual reload.
- Stopping the Python server shows an update-failure warning; restarting it recovers automatically on the next refresh.
- Values and family wording have been compared with your trusted Panchanga/teacher, especially on lunar-new-year and leap-month dates.

The month/year calculations now handle Adhika/Nija and regular-Chaitra turnover. For the selected DrikGanita reference, save Hindu sunrise, solar Ritu and exact regular-Chaitra new-moon year turnover in Household settings; retain a different convention only if your family requires it. The three original reference dates pass and the broader DrikGanita comparison is partial; see validation/reports/SUMMARY.md for coverage. Teacher wording review remains necessary. Kshaya months explicitly require manual recital review.

For your supplied text, use **My family Sankalpa**. US cities use your supplied section with the existing opening and selected session closing. Other countries use the standard expanded wording. Select Kannada, Sanskrit or English transliteration independently; the calendar fields remain dynamic. The audio button now generates only the eight changing calendar phrases. The full family text is excluded; each request is still checked against the 100-syllable limit.

Use **Edit wording** or **Add variation** beside the reader. Insert daily fields from the editor dropdown and save once for all three scripts. **Cancel** keeps the saved wording. Variations stay on this browser, apply to their creation country, and can be hidden/recovered. The built-in expanded/short alternatives are no longer in the everyday selector.
