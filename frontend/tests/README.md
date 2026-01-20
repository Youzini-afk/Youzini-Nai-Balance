## Frontend E2E Tests (Playwright)

Prerequisites:
- Backend running at `http://localhost:5002`
- Frontend served (for example with a static server)

Setup:
```bash
cd frontend
npm init -y
npm install -D @playwright/test
npx playwright install
```

Run:
```bash
npx playwright test tests/e2e.spec.js
```

Notes:
- Update credentials and URL in `tests/e2e.spec.js` as needed.
- Make sure CORS and API base URLs are aligned.

