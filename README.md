# 🔬 Control Systems Laboratory Incident Reporting System

## Overview

The Control Systems Laboratory Incident Reporting System is a robust web-based platform designed to facilitate the reporting, tracking, and management of incidents within control systems laboratories. It empowers students, instructors, and laboratory personnel to efficiently document issues, monitor resolution progress, and maintain a safe laboratory environment.

## Features

- **Secure Authentication**: Role-based access for students, instructors, and administrators
- **Incident Reporting**: Comprehensive forms for equipment and safety incidents
- **Status Tracking**: Real-time updates on incident resolution
- **Dashboard**: Visual analytics of incidents and trends
- **Notifications**: Automated alerts for stakeholders
- **Responsive Design**: Accessible from desktops, tablets, and mobile devices
- **Integrated Documentation**: Access to equipment manuals and safety protocols

## Architecture

This system follows a Model-View-Controller (MVC) architecture:

```
systems-laboratory-control/
├── app/
│   ├── controllers/    # Route handlers and business logic
│   ├── models/         # Database models and data access layer
│   ├── services/       # Business services and utilities
│   ├── static/         # CSS, JavaScript, and images
│   ├── templates/      # HTML templates
│   └── __init__.py     # Application factory
├── static/             # CSS, JS, images
├── templates/          # HTML templates (if not in app/)
├── .env                # Environment variables (do not commit to git)
├── .gitignore          # Git ignore file
├── requirements.txt    # Project dependencies
├── Procfile            # Render start command
└── app.py              # Application entry point
```

## Installation

### Prerequisites

- Python 3.8 or newer
- pip (Python package installer)
- Recommended: Python virtual environment

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/jairdevl/control-systems-laboratories.git systems-laboratory-control
   cd systems-laboratory-control
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   ```
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     If you encounter a script execution policy error, run PowerShell as Administrator and execute:
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```
   - **Windows (cmd):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root with:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   ```

## Running the Application

### Development Server
To start the development server:
```bash
python app.py
```

The application will be available at [http://localhost:5000](http://localhost:5000) by default.

## Deployment

### Apache + mod_wsgi (Recommended for Production)

Below is an example Apache VirtualHost configuration for deploying this application with mod_wsgi:

```apache
<VirtualHost *:80>
    ServerAdmin youremail@example.com
    WSGIDaemonProcess system_laboratory_control python-home=/var/www/system-laboratory-control/venv python-path=/var/www/system-laboratory-control
    WSGIProcessGroup system_laboratory_control
    WSGIScriptAlias / /var/www/system-laboratory-control/app.wsgi

    <Directory /var/www/system-laboratory-control>
        Require all granted
        Options -Indexes +FollowSymLinks
        AllowOverride None
    </Directory>
</VirtualHost>
```
- Adjust paths and email as needed for your environment.
- Ensure `mod_wsgi` is installed and enabled on your Apache server.

### Render.com (Alternative Cloud Deployment)
1. Push your code to a GitHub repository.
2. Create a new Web Service at [https://dashboard.render.com/](https://dashboard.render.com/).
3. Connect your repository and select Python as the environment.
4. Add required environment variables:
    - DB_HOST
    - DB_PORT
    - DB_NAME
    - DB_USER
    - DB_PASSWORD
5. Ensure a `Procfile` exists with:
    ```
    web: gunicorn app:app
    ```
6. Render will auto-deploy on each push.

To run with Gunicorn locally:
```bash
pip install gunicorn
gunicorn -w 4 "run:create_app()"
```

## Usage

1. Register using your institutional email address.
2. Log in to the system.
3. Access the dashboard to view incident statistics.
4. Report incidents via the "New Incident Report" form.
5. Track your reports under "My Reports".
6. Administrators can manage users and review all reports from the admin panel.

## Testing

Run the test suite with:
```bash
python -m pytest
```

## Documentation

- Full documentation is available in the `docs/` directory.
- API documentation is accessible at `/api/docs` when the application is running.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to your branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, contact the maintainer: [jairenriquez1715@gmail.com]
