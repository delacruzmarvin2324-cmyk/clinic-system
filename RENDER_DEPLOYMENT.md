# Deploy the clinic API on Render

The Flutter APK needs a public HTTPS API URL to work outside your local Wi-Fi. This repo includes a Render Blueprint for the Django API and a persistent PostgreSQL database.

## Before deploying

- Create a GitHub repository and push this project. The root `.gitignore` excludes `db.sqlite3`, virtual environments, environment files, and generated static files. Keep `appointment_model.pkl` in the repository because the API uses it for predictions.
- The Render Blueprint creates a web service and PostgreSQL database. Review the selected plans and prices in Render before applying it; this file intentionally does not select a plan.
- Render's free web services sleep when idle, and its free PostgreSQL databases expire after 30 days and are deleted after the grace period. Use paid persistent hosting for a service that must stay available. Do not put real patient information on free hosting; review applicable privacy and security requirements before using patient data in production.
- The hosted database starts empty. The local SQLite database is not uploaded or migrated by this setup.

## Deploy

1. Push the repo to GitHub.
2. In Render, choose **New +** then **Blueprint**, connect the GitHub repo, and apply its `render.yaml`.
3. After the deploy completes, copy the service's public HTTPS URL, for example `https://clinic-api-xxxx.onrender.com`.
4. In the Render dashboard, open the `clinic-api` service's **Environment** settings and add these variables for the first doctor account:

	- `INITIAL_DOCTOR_USERNAME`
	- `INITIAL_DOCTOR_PASSWORD`
	- `INITIAL_DOCTOR_FIRST_NAME`
	- `INITIAL_DOCTOR_LAST_NAME`
	- `INITIAL_DOCTOR_EMAIL`
	- `INITIAL_DOCTOR_SPECIALTY`
	- `INITIAL_DOCTOR_CONTACT_NUMBER`

	Use a unique, strong password and keep it in Render's environment settings; do not commit it to the repository. Save the changes and deploy. The service startup migrates the database and creates the doctor if that username does not already exist. If no initial doctor variables are set, provisioning is skipped. Existing doctor accounts are not assigned a new password.

## Build the APK for the hosted API

From the `mobile` directory, replace the example host with the actual Render service URL:

```powershell
flutter build apk --release "--dart-define=API_BASE_URL=https://clinic-api-xxxx.onrender.com/api"
```

The APK is written to `mobile/build/app/outputs/flutter-apk/app-release.apk`. Install it on the phone and test login while the Render service is deployed. No local Django server is needed for the hosted build.

If you later host the Flutter web client on a different domain, add that exact origin to the Render service's `DJANGO_CORS_ALLOWED_ORIGINS` environment variable.