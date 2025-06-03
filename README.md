# WhatMusicDoILike? Backend

## Overview
This code package contains the backend logic for providing the playlist transferring service from Youtube Music to Spotify, via the Spotify Web API, Google YoutubeMusic API. This is a Flask-based backend application using SQLAlchemy for database management. The project follows a modular structure, with database models defined in `/app/models` and API endpoints located in `/app/routes`.

## Project Structure
```
/app
  |-- models/       # Contains database table definitions
  |-- routes/       # Contains API endpoint implementations

```

## Technologies Used
- **Flask**: Lightweight web framework for Python
- **SQLAlchemy**: ORM for database interactions
- **Python**: Programming language for backend development

## API Endpoints
All API endpoints are defined in the `/app/routes` directory.

## Database Models
All database table definitions are found in `/app/models`, using SQLAlchemy.
