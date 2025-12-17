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
SUPABASE_KEY=your_supabase_anon_key
MAPBOX_ACCESS_TOKEN=your_mapbox_access_token
```

**Note:** Use the **anon key** (not service_role key) for public deployments. Storage bucket policies must be configured in Supabase to allow anon uploads.

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
| `SUPABASE_KEY` | Supabase anon key (for public deployments) | Yes |
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

https://web-application-2025-group-1-162u.onrender.com/

## License

This project was developed as part of an academic collaboration and is subject
to a Technology/IP Transfer and Non-Compete Agreement with a collaborating entity.

All intellectual property rights to the developed MVP are governed by this
agreement.

This codebase is proprietary. No use, reproduction, modification, distribution,
or publication of this software or its underlying concepts is permitted, except
by parties explicitly authorized under the aforementioned agreement, or with
prior written permission from the rights holder(s).

### Feedback Sessions

Feedback Session 1: https://teams.microsoft.com/l/meetingrecap?driveId=b%21rNRqaAAqTkKdRksENzaR2VvXSBITKwhJpaOylnPwlxJ9H5mY8hjGQba7pqyD_RBO&driveItemId=01U2ZX7AYEVAVSQZHYDZBYXWZ2PBUI3BRQ&sitePath=https%3A%2F%2Fugentbe-my.sharepoint.com%2F%3Av%3A%2Fg%2Fpersonal%2Fthomas_derave_ugent_be%2FEQSoKyhk-B5Di9s6eGiNhjABm3bfjMLU1YbB9DNtouierQ&fileUrl=https%3A%2F%2Fugentbe-my.sharepoint.com%2Fpersonal%2Fthomas_derave_ugent_be%2FDocuments%2FOpnamen%2FJaron%2520Decaluw%25C3%25A9%2520-%2520Meeting%2520Thomas%2520Derave-20251127_133346-Opname%2520van%2520vergadering.mp4%3Fweb%3D1&iCalUid=040000008200E00074C5B7101A82E008000000005F5C7321ED5DDC01000000000000000010000000EE668D953FF8DF4DAA687131C61C2FA8&threadId=19%3Ameeting_OWE2MGViMjEtZmE0NC00MzNmLTgxODktMWQ4ODJmODFjY2Mz%40thread.v2&organizerId=5e3bf669-032c-4afa-8733-0b0189341717&tenantId=d7811cde-ecef-496c-8f91-a1786241b99c&callId=5fb68d26-f8fc-44b0-b6b8-5eae11b78b25&threadType=Meeting&meetingType=Scheduled&subType=RecapSharingLink_RecapCore

Feedback Session 2: https://teams.microsoft.com/l/meetingrecap?driveId=b%21rNRqaAAqTkKdRksENzaR2VvXSBITKwhJpaOylnPwlxJ9H5mY8hjGQba7pqyD_RBO&driveItemId=01U2ZX7AZ7LCOTBMDKLJFYENJ56WMBD5YD&sitePath=https%3A%2F%2Fugentbe-my.sharepoint.com%2F%3Av%3A%2Fg%2Fpersonal%2Fthomas_derave_ugent_be%2FET9YnTCwalpLgjU99ZgR9wMBplLo0Qm4Z4ouycwPnNcHDQ&fileUrl=https%3A%2F%2Fugentbe-my.sharepoint.com%2Fpersonal%2Fthomas_derave_ugent_be%2FDocuments%2FOpnamen%2FJaron%2520Decaluw%25C3%25A9%2520-%2520Meeting%2520Thomas%2520Derave-20251208_130155-Opname%2520van%2520vergadering.mp4%3Fweb%3D1&iCalUid=040000008200E00074C5B7101A82E0080000000028D755441F65DC0100000000000000001000000007E7DD66E8E2D44F897AC9D6C7B7E396&threadId=19%3Ameeting_ZmRmYjJlOWYtMDE2NC00YjNmLTgxNmUtZDYyYTk0YTVmMTU0%40thread.v2&organizerId=5e3bf669-032c-4afa-8733-0b0189341717&tenantId=d7811cde-ecef-496c-8f91-a1786241b99c&callId=d197b441-7d23-4289-8c09-c4ee72a86e9b&threadType=Meeting&meetingType=Scheduled&subType=RecapSharingLink_RecapCore
