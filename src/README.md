# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements
- Manage announcements (signed-in staff only)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                                     | Description                                              |
| ------ | ---------------------------------------------------------------------------- | -------------------------------------------------------- |
| GET    | `/activities`                                                                | Get all activities with their details                    |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`           | Sign up a student for an activity (teacher authenticated) |
| POST   | `/activities/{activity_name}/unregister?email=student@mergington.edu`       | Unregister a student from an activity (teacher authenticated) |
| POST   | `/auth/login?username={username}&password={password}`                        | Sign in as a staff user                                  |
| GET    | `/auth/check-session?username={username}`                                    | Validate an existing staff session                       |
| GET    | `/announcements`                                                             | Get currently active announcements                       |
| GET    | `/announcements/manage?teacher_username={username}`                          | Get all announcements for management (signed-in staff)   |
| POST   | `/announcements?teacher_username={username}`                                 | Create announcement (requires `message` and `expiration_date`) |
| PUT    | `/announcements/{announcement_id}?teacher_username={username}`               | Update announcement                                      |
| DELETE | `/announcements/{announcement_id}?teacher_username={username}`               | Delete announcement                                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB. The app initializes sample activities, teacher accounts, and an example announcement when collections are empty.
