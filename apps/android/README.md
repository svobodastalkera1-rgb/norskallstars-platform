# NorskAllstars Android

Native Kotlin/Jetpack Compose online client against existing versioned backend
APIs. Phase 6 is implemented locally; hosted/Owner acceptance is not claimed.
Presentation/ViewModel/network/platform boundaries live under `app/src/main`.
No Course Package interpretation, offline queue, private content or signing keys.

Toolchain: JDK 17 (local/CI Microsoft 17.0.20.1), Gradle 9.6.0 with distribution
and wrapper SHA-256 verification, AGP 9.4.1 and Kotlin/Compose compiler 2.4.20.
CI installs the exact Microsoft archive with a pinned SHA-256; `setup-java` uses
`jdkfile` with SemVer cache label `17.0.20`, then verifies the actual installed
Microsoft `17.0.20.1` identity. The vendor resolver cannot handle its fourth
version component. No floating Java version or older patch is substituted.
Compile/target API 36, build tools 36.0.0, minimum API 26. Final supported-device
and store requirements need later release acceptance; no store publication occurs.
Dependency locks/checksums cover resolved artifacts; audit findings must be resolved
or reported explicitly. No public APK/report/credential artifacts are uploaded.

Install the pinned JDK and Android command-line tools using their official
distributions. Set `JAVA_HOME`, `ANDROID_HOME` and add `$ANDROID_HOME/platform-tools`
to PATH. Install `platform-tools`, `platforms;android-36`, `build-tools;36.0.0`,
`emulator` and `system-images;android-35;default;x86_64` with Android SDK tooling.
Keep tool installations and local properties outside tracked source. Accept SDK
terms through the installed tooling; SDK licenses are separate from this project's
pending license choice. Do not introduce production credentials to local commands.

Lint treats correctness, accessibility and security warnings as errors. Its four
network-dependent update suggestions (`GradleDependency`, `NewerVersionAvailable`,
`AndroidGradlePluginVersion`, `OldTargetApi`) are excluded: API 36 and the AGP 9.4
compatible Gradle version are deliberate pins, not a claim of final store/device
acceptance. OSV auditing covers app, test, lint and buildscript dependency locks;
Dependabot proposes upgrades. Known vulnerable transitive libraries are upgraded
explicitly, never excluded from the security audit. Reassess target SDK and the
supported-device matrix before Release Candidate/Google Play acceptance.

From repository root:

```sh
make android-check
make android-build
make android-audit
```

Default debug API is `http://10.0.2.2:8000`, the emulator's host loopback alias.
Start the documented local backend/PostgreSQL, apply migrations, and include
`10.0.2.2` in that development backend's allowed hosts. HTTP is permitted only
for the debug emulator/loopback allowlist; release builds require HTTPS/system trust.
For physical-device development use `adb reverse tcp:8000 tcp:8000` and build
with `-PdevelopmentOrigin=http://127.0.0.1:8000`, or an explicitly configured
HTTPS staging origin. Never make backend/DB ports public to work around access.
Install debug APK via Android Studio or `adb install -r app/build/outputs/apk/debug/app-debug.apk`.

For manual testing while the backend runs in Codespaces, forward its port privately
to your computer in VS Code. A desktop emulator can use `10.0.2.2:8000` to reach
that local forwarded port. For a USB-connected phone, run `adb reverse` on your
computer and use the loopback debug origin above. Install the debug APK privately
from the Codespace workspace; neither downloading the whole repository nor
making backend/DB ports public is required. A headless Codespace emulator runs
automated tests, not a browser-accessible Android UI. Keep test APKs out of Git.

The default runtime has no corpus/users. Register and confirm email using the
documented private development outbox or verify the existing email link in Web,
then sign in to Android. The app also supports manual verification/reset tokens;
use the decoded complete token, not raw MIME/quoted-printable. Local outbox does
not send live mail. No production SMTP/Google credentials are needed for email
flows. The safe synthetic scenario below exercises the complete learning path.

## Isolated real-backend device tests

```sh
python3 scripts/phase1.py init
python3 scripts/android_e2e.py prepare
python3 scripts/android_e2e.py serve
```

`prepare` resets only `norskallstars_android_test`, derives the approved public
synthetic package through the existing test mechanism, and stores generated
test credentials only in ignored mode-600 staging. It never resets ordinary or
manual-review databases. Create an API 35 default x86_64 AVD with `avdmanager` (or Android Studio), and
start it with KVM. For headless CI-like runs:

```sh
emulator -avd YOUR_AVD -no-window -no-audio -no-snapshot -gpu swiftshader_indirect -idle-grpc-timeout 3600 -memory 1536 -cores 2
```

Keep emulator/adb/gRPC ports local. The explicit gRPC idle timeout is bounded;
it does not prevent other emulator/process failures. Stop the emulator after testing. Then
in another terminal from repository root:

```sh
cd apps/android
./gradlew :app:assembleDebug :app:assembleDebugAndroidTest -PdevelopmentOrigin=http://10.0.2.2:8001 --no-daemon
cd ../..
adb install -r apps/android/app/build/outputs/apk/debug/app-debug.apk
python3 scripts/android_e2e.py device-input
python3 scripts/android.py device
```

Connected tests may uninstall the app when finished. If the debug app remains
installed, clear its data after testing with `adb shell pm clear
com.norskallstars.platform.dev`.

Use an isolated test AVD: `device-input` first clears this debug app's data/session.
Device inputs are placed only in the debuggable app's private files; the test
consumes/deletes them. Never attach generated login files, test reports, emulator
logs/screenshots or recordings to public PRs. Re-prepare/re-provision before
repeating the destructive synthetic account-erasure journey. App-private temporary
media and sensitive credentials are cleaned; this is not Phase 7 offline support.

Release builds default to an invalid HTTPS origin and have no signing configuration.
For authorized staging, `-PapiOrigin=https://your-approved-api.example` configures
the public API origin and `-PgoogleClientId=your-public-client-id.apps.googleusercontent.com`
configures Credential Manager. The backend must allow the same audience; Android
provider registration/signing fingerprint and live Google/SMTP acceptance remain
Owner staging actions. These identifiers are public configuration, never secrets.

See [scope](../../docs/android/README.md) and [ADR 0014](../../docs/adr/0014-native-android-online.md).
The [Product Owner manual-review guide](../../docs/android/manual-review.md) gives
the complete private Codespace-to-device installation, account/course walkthrough,
Android-specific development mailbox command and explicit coverage limits.
