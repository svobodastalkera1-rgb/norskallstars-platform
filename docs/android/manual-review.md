# Phase 6 Product Owner Android review

Use a private debug build and synthetic test database. No Google Play publication,
production credentials, SMTP account, private corpus or repository clone on your
desktop is required. The headless Codespace emulator is for automated checks; a
desktop Android Studio emulator or USB-connected phone provides the interactive UI.

## Start the isolated backend in Codespaces

From the repository root, with Docker and the documented uv environment available:

```sh
python3 scripts/phase1.py init
python3 scripts/android_e2e.py prepare
python3 scripts/android_e2e.py serve
```

Leave the last command running in its terminal. `prepare` applies migrations and
resets **only** `norskallstars_android_test`, then creates the public-safe synthetic
course and two verified synthetic accounts. It resets their progress/passwords;
do not run it while retaining a previous Android review session. Ordinary local,
Web and manual-review databases are not reset. The backend binds to loopback port
**8001**; PostgreSQL remains loopback-only on **5433**. The health URL is
`http://127.0.0.1:8001/health/ready` and must return `{"status":"ready"}`.
If an existing `android_e2e.py serve` instance already owns port 8001, reuse that
instance or stop it before starting a replacement; do not run two servers on the
same port or substitute the ordinary development database.

In desktop VS Code connected to this Codespace, forward **8001** in the Ports tab,
keep visibility **Private**, and confirm its local forwarded port is also **8001**.
If VS Code assigns another local port, use that number in the following desktop
origin/reverse commands. Do not forward PostgreSQL or expose the backend publicly.

## Build and install privately

Use the pinned JDK/SDK described in [Android setup](../../apps/android/README.md).
Build in Codespaces for a desktop emulator:

```sh
cd apps/android
./gradlew :app:assembleDebug -PdevelopmentOrigin=http://10.0.2.2:8001 --no-daemon
```

For a USB-connected physical device build instead with
`-PdevelopmentOrigin=http://127.0.0.1:8001`. Both origins are debug-only allowlisted
loopback addresses. Release HTTPS/signing/store setup is outside this review.

Save `apps/android/app/build/outputs/apk/debug/app-debug.apk` to your computer using
VS Code's file download/save functionality. This ignored APK is a private review
build; do not add it to Git, a public release or a PR attachment.

On your computer, start an Android Studio emulator (API 26 or newer; API 35 is the
newer automated baseline), or connect an Android 8+ phone with USB debugging enabled.
Use the local Android SDK `adb`:

```sh
adb devices
adb install -r /path/to/app-debug.apk
adb shell am start -n com.norskallstars.platform.dev/com.norskallstars.platform.MainActivity
```

For a USB phone, run `adb reverse tcp:8001 tcp:8001` before starting the app. Use
`adb -s DEVICE_SERIAL ...` for each command if multiple devices are connected.
For the desktop emulator, `10.0.2.2` reaches your computer's privately forwarded
port; no `adb reverse` is needed. Open the installed **NorskAllstars** debug app.
Check the private forwarding tunnel/backend if sign-in reports a network failure.
If installation reports `INSTALL_FAILED_UPDATE_INCOMPATIBLE` from a previous debug
build signed on another machine, uninstall **only this debug app** with
`adb uninstall com.norskallstars.platform.dev`, then install again. This clears its
local session and temporary files, not the backend account; do not uninstall the
production app or disable Android signature verification.

## Account and course walkthrough

Privately open `.cache/android-e2e/login.json` in Codespace VS Code and use the email
and password under `accounts["android:learning"]`. They are already verified and
generated anew on preparation. Never paste credentials, responses, recordings or
private screenshots into a public PR. The `android:accessibility` account is separate
and useful for isolation and accessibility review.

1. Sign in; switch Bokmål/English in the account preferences. Check loading/error/
   empty states, scrolling, device back, large font and TalkBack focus/labels.
2. Start the synthetic course. Optionally take placement; choose the correct option
   specified by the local `scenario.correct_choice` and acknowledge activities.
   Accepting the recommendation must not create completion or mastery.
3. Continue the first lesson, view its synthetic image, start an attempt, select
   the correct option, acknowledge each required activity and submit. Progress
   unlocks the next unit only from the backend result. Translation is offered only
   when the content actually includes an explicit translation.
4. Replay the completed lesson with `scenario.alternative_choice`. The previous
   canonical completion remains; replay does not add duplicate completion credit.
5. Complete the second lesson: match **yellow square → water** and **blue circle →
   shade**, enter an invented response such as “An invented square signals water”,
   acknowledge the required activities and submit. The synthetic rubric result
   remains pending; its explicit test policy allows completion without fabricating
   a grade. Both primary synthetic lessons are completable.
6. Review dashboard and private attempt history. Time is approximate submitted
   active-attempt time: interact during a running attempt for about seventy seconds,
   then submit and reload the dashboard. Idle/background time is not credited.
7. Rotate/recreate the app, background/foreground it, close and restart it. Confirm
   the session survives normal recreation and the course remains pinned. Temporarily
   interrupt the backend/tunnel: errors must be clear and no offline synchronization
   or automatic replay of a mutating request should be claimed.
8. Review sessions on a second device, revoke a session, log out and sign in as the
   other account. Prior-account progress/media must not appear. Review password
   change with fresh proof; keep the resulting password locally if continuing.
9. Test account deletion **last** with the current password and explicit confirmation.
   It erases account-owned learning/audio state and the native session. Re-prepare
   the dedicated synthetic database for a new review; old app sessions need clearing.

## Registration/recovery without external providers

The default outbox does **not** send live email. To review registration, use a new
synthetic `@example.com` address and the app's verification screen. After requesting
verification or password reset, drain the outbox for **this Android database**, not
the ordinary development database. From repository root:

```sh
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts').resolve()))
import android_e2e
import phase1
phase1.run(phase1.uv('python', '-m', 'norskallstars_backend.identity.cli', 'mail',
    '--private-directory', str(Path('.cache/android-e2e/identity-mail').resolve())),
    env=android_e2e.environment())
PY
```

Read the generated private `.eml` in that ignored directory using a MIME-aware
viewer. Use the **complete decoded token** from the verification/reset link in the
native token field, not the URL, raw quoted-printable text, folded lines or a reset
token in the verification screen. Tokens are one-use and expiring; request a fresh
one after consumption/expiry. The CLI prints counts only. Never publish the mail
files/token or change provider credentials to make this local review work.

## Coverage limits and separate gates

The primary approved synthetic course has image/choice/matching/rubric activities;
it contains **no speech activity or playable audio asset**. Therefore it cannot
exercise the microphone consent/upload UI or course-audio playback manually.
Do not replace it with real/private content to hide this limit. Native instrumentation
separately tests real microphone/private recording/playback/lifecycle and Keystore;
JVM tests exercise consent/selection/upload/withdrawal boundaries, and backend
regressions exercise synthetic speech/media ownership and retention. Those checks
do not claim a manual speaking-course acceptance or real pronunciation evaluation.

Live Google Credential Manager needs Owner-configured staging provider/client ID
and the appropriate Android signing fingerprint. Live SMTP needs staging delivery
acceptance. Neither is verified by this default local runtime. Remote storage,
scheduled retention/GC/backups, privacy export, administrator permissions, explicit
release migration, license and store/signed-production release acceptance remain
later gates. Do not enable them for this review or start Phase 7.
