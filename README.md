# Jadwal Stream

A Flask-based web application for managing YouTube live stream schedules with automated scheduling capabilities.

## Features

- Create and manage YouTube live stream schedules
- Automated stream scheduling
- YouTube token management
- Stream key management
- Customizable auto-scheduling times
- Thumbnail management
- Privacy settings control
- Integration with YouTube API

## Prerequisites

- Python 3.7 or higher
- Google account with YouTube streaming enabled
- `client_secret.json` file from Google Cloud Console (YouTube Data API v3)

## Required Python Modules

```bash
pip install -r requirements.txt
```

Contents for requirements.txt:
```
flask
pandas
pytz
google-auth-oauthlib
schedule
openpyxl
```

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google OAuth:
   - Go to Google Cloud Console
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `client_secret.json` in the project root directory

## Configuration Files

The application uses several configuration files:

- `client_secret.json`: Google OAuth credentials
- `schedule_config.json`: Auto-scheduling time configurations
- `stream_mapping.json`: Stream key mappings
- `scheduler_status.json`: Scheduler status tracking
- `live_stream_data.xlsx`: Main schedule database

## Running the Application

1. Ensure all configuration files are in place

2. Start the Flask application:
```bash
python app.py
```

3. Access the application:
   - Open a web browser and navigate to `http://localhost:5000`
   - For network access, use `http://<your-ip>:5000`

## Application Structure

- `/templates`: HTML templates for the web interface
- `/thumbnails`: Directory for stream thumbnail storage
- `app.py`: Main application file
- `live.py`: YouTube live streaming functionality
- `kunci.py`: Stream key management
- Other supporting Python modules for specific functionalities

## Features Usage

### Token Management
- Create new YouTube API tokens
- Delete existing tokens
- View available tokens

### Stream Management
- Create new stream schedules
- Edit existing schedules
- Delete schedules
- Configure auto-start and auto-stop
- Set privacy status
- Upload thumbnails

### Auto-Scheduling
- Configure schedule check times
- Enable/disable auto-scheduling
- View scheduler status
- Manual schedule execution

## Important Notes

1. Ensure your Google account has YouTube streaming enabled
2. Keep your `client_secret.json` secure and never share it
3. The application stores tokens in JSON files - keep them secure
4. The scheduler runs every minute to check for scheduled streams
5. All times are handled in Asia/Jakarta timezone by default

## Error Handling

- The application includes comprehensive error logging
- Check the console output for detailed error messages
- Flask debug mode is enabled by default for development

## Security Considerations

- Keep all JSON token files secure
- Don't expose the application to the public internet without proper security measures
- Use environment variables for sensitive configurations in production

## Customization

You can customize various aspects of the application:
- Modify `TIMEZONE` in `app.py` to change the default timezone
- Adjust scheduler check intervals in the scheduler thread
- Customize the web interface through the templates