# MediCare Flutter client

The Flutter client uses the existing Django database and REST API. Appointment no-show predictions continue to run through the existing Python/scikit-learn model; the model file and inference code are not duplicated in Dart.

## Run locally

From the project root, start Django:

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

In another terminal, start the Flutter web client:

```powershell
cd mobile
flutter pub get
flutter run -d chrome --web-port 8080
```

The default API address is `http://127.0.0.1:8000/api` for web, desktop, and iOS simulators, and `http://10.0.2.2:8000/api` for Android emulators. Override it with `--dart-define=API_BASE_URL=http://your-host:8000/api` when running on a physical device or another deployment.

For web development, Django allows the localhost Flutter ports by default. Set `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_ALLOWED_HOSTS` to explicit comma-separated values for other origins and hosts.
