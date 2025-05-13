# Multi-Mac Setup Guide for `emaillm-ws`

This guide helps you set up and sync your development environment for `emaillm-ws` across multiple Macs (e.g., MBP13, MBP16).

---

## 1. Dropbox Project Path
- Ensure your project is at:
  `/Users/mthompson/Dropbox/github/emaillm-ws`

## 2. Install Dependencies
```sh
pip install -r requirements.txt
```

## 3. Environment Variables (.env)
Create a `.env` file in your project root with the following content:

```env
# .env for emaillm-ws
GOOGLE_APPLICATION_CREDENTIALS=/Users/mthompson/Dropbox/secrets/your-service-account.json
SENDGRID_SIGNING_KEY=your_sendgrid_signing_key_here
OPENAI_API_KEY=your_openai_api_key_here
# Add any other keys as needed
```

- Update the file paths and keys as appropriate for your machine.

## 4. Required Files to Copy from MBP16
- `.env` (if it already exists)
- The Google Cloud service account JSON file referenced above
- Any other config or secret files referenced in your `.env` or by your app

## 5. Test Your Setup
```sh
pytest -q
```
- All tests should pass. If not, check for missing env vars or secrets.

## 6. Service-Specific Setup
### Firestore / Google Cloud
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account file with Firestore access.

### SendGrid
- Ensure `SENDGRID_SIGNING_KEY` is present in your `.env`.
- To test inbound parse locally, use:
  ```sh
  scripts/sendgrid_curl_test.sh
  ```

### OpenAI / GPT-4.1
- Ensure `OPENAI_API_KEY` is set if your app uses OpenAI.

## 7. Deployment & Live Testing
- Deploy with:
  ```sh
  windsurf deploy --prod
  ```
- Set SendGrid's inbound parse destination to your deployed `/webhook/inbound` URL.
- Send a test email (e.g., to `manutd@emaillm.com`) and verify round-trip.

---

## Troubleshooting
- If tests fail, check for missing or incorrect `.env` or secrets.
- If Firestore or SendGrid features fail, double-check credentials and permissions.
- For new dependencies or services, update this guide and your `.env` accordingly.

---

**Keep this file updated as your stack evolves!**

If you have questions or need to onboard a new device, refer to this guide first.
