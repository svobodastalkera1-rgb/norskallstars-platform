# NorskAllstars Web

Phase 5 React/TypeScript client: Bokmål-first, responsive and accessible. It uses
versioned Identity/Learning/Media HTTP contracts. The backend owns evaluation,
progress, access and release pinning; the client never reads Course Package files.

Node 24.21.0 and the committed npm lock are required. From this directory:

```sh
npm ci --ignore-scripts
npm run dev
npm run format
npm run lint
npm run build
npm test
npm run contracts
```

Development server: http://127.0.0.1:3000; API proxy: 127.0.0.1:8000. The backend
must explicitly allow the development origin. For the complete local runtime,
synthetic browser tests and configuration see [development](../../docs/development.md).
Production build is served by the backend image; no deployment is authorized.

Credentials live only in tab memory. Reload requires sign-in. Private microphone
blobs remain in memory unless separate consent and server sampling permit upload;
no browser storage, service worker, automatic microphone access or ML processing.
Use account settings to withdraw retained recordings after a fresh sign-in.

Google requires a public build-time VITE_GOOGLE_CLIENT_ID matching an explicitly
configured backend audience. Client IDs are public identifiers, never provider
secrets. Missing configuration is shown truthfully. Live Google/SMTP acceptance,
private remote-storage verification and production operations remain separate gates.
Android and offline behavior are outside this phase. License remains Owner-pending.
