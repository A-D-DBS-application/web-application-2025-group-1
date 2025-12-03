"""
Migration script to populate Destination table with initial data.
Run this once after adding the Destination model.
"""
from app import create_app
from app.models import db, Destination

def migrate_destinations():
    """Add initial destinations to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if destinations already exist
        if Destination.query.count() > 0:
            print("Destinations already exist in database. Skipping migration.")
            return
        
        # Create initial destinations
        destinations = [
            Destination(
                name='South Africa',
                flag_emoji='🇿🇦',
                country_code='SA',
                image_path='img/south-africa.webp',
                is_active=True
            ),
            Destination(
                name='Morocco',
                flag_emoji='🇲🇦',
                country_code='MO',
                image_path='img/morocco.jpg',
                is_active=True
            )
        ]
        
        for dest in destinations:
            db.session.add(dest)
        
        db.session.commit()
        print(f"Successfully added {len(destinations)} destinations to database.")

if __name__ == '__main__':
    migrate_destinations()

