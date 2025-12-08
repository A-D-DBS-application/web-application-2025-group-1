[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22401afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a.DxqGVQx4)
# AfriGuide - African Travel Itinerary Planner

A Flask-based web application for planning and managing personalized African travel itineraries.

## Features

- 🗺️ Interactive map-based itinerary planning
- 📍 Activity management with filtering
- 👥 Multi-traveller support
- 🏢 Travel agency integration
- 📸 Image storage via Supabase Storage
- 🎨 Modern, responsive UI

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database (Supabase)
- Supabase account for storage
- Mapbox account for maps

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd web-application-2025-group-1
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:

```env
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
MAPBOX_ACCESS_TOKEN=your_mapbox_access_token
```

**Important:** Never commit the `.env` file to version control!

### Database Setup

Run migrations:
```bash
flask db upgrade
```

### Running the Application

Development:
```bash
python run.py
```

Production (with Gunicorn):
```bash
gunicorn app:app
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase service_role key | Yes |
| `MAPBOX_ACCESS_TOKEN` | Mapbox API access token | Yes |

## Project Structure

```
app/
├── __init__.py          # Flask app factory
├── config.py            # Configuration
├── models.py            # Database models
├── routes.py            # Application routes
├── storage.py           # Supabase Storage utilities
├── templates/           # Jinja2 templates
├── static/              # CSS, JS, images
└── utils.py             # Utility functions
```

## Deployment

### Render.com

1. Connect your GitHub repository
2. Set all required environment variables in Render dashboard
3. Deploy!

## License

[Your License Here]
