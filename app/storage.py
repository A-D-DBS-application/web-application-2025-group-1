"""
Supabase Storage utilities for uploading and managing images.
"""
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
import os

# Supabase client instance (lazy initialization)
_supabase_client = None


def get_supabase_client():
    """Get or create the Supabase client instance."""
    global _supabase_client
    
    try:
        # Always try to get config values (in case they changed)
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_KEY')
        
        if not url:
            print("Error: SUPABASE_URL not found in configuration")
            _supabase_client = None
            return None
        if not key:
            print("Error: SUPABASE_KEY not found in configuration")
            _supabase_client = None
            return None
        
        # If client doesn't exist, create new client
        if _supabase_client is None:
            try:
                from supabase import create_client
                _supabase_client = create_client(url, key)
                print(f"Supabase client initialized successfully with URL: {url}")
            except ImportError as e:
                print(f"Error: supabase package not installed: {e}")
                print("Please install it with: pip install supabase")
                _supabase_client = None
                return None
            except Exception as e:
                print(f"Error: Could not initialize Supabase client: {e}")
                print(f"URL: {url}")
                print(f"Key: {'Set' if key else 'Not set'}")
                _supabase_client = None
                return None
        
        return _supabase_client
    except RuntimeError as e:
        # Outside of application context
        print(f"Error: Cannot access Flask application context: {e}")
        return None
    except Exception as e:
        print(f"Error: Unexpected error in get_supabase_client: {e}")
        return None


def upload_file_to_supabase(file, bucket_name, folder=""):
    """
    Upload a file to Supabase Storage.
    All uploads must go to Supabase - no local fallback.
    
    Args:
        file: FileStorage object from Flask request
        bucket_name: Name of the Supabase storage bucket
        folder: Optional folder path within the bucket
    
    Returns:
        tuple: (success: bool, file_path: str or error_message: str)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check if supabase package is installed
    try:
        import supabase as supabase_module
    except ImportError:
        return False, "Supabase package not installed. Please run: pip install supabase"
    
    supabase = get_supabase_client()
    
    if supabase is None:
        # Get more specific error information
        try:
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            if not url:
                return False, "SUPABASE_URL not configured. Please check your configuration."
            if not key:
                return False, "SUPABASE_KEY not configured. Please check your configuration."
            return False, "Supabase client initialization failed. Check console for details."
        except Exception as e:
            return False, f"Error accessing configuration: {e}"
    
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{original_filename}"
        
        # Build the file path
        if folder:
            file_path = f"{folder}/{unique_filename}"
        else:
            file_path = unique_filename
        
        # Read file content
        file_content = file.read()
        
        # Get content type
        content_type = file.content_type or 'application/octet-stream'
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": content_type}
        )
        
        # Return the file path (not the full URL - we'll build that when displaying)
        return True, file_path
        
    except Exception as e:
        error_msg = f"Error uploading to Supabase: {e}"
        print(error_msg)
        return False, error_msg


def delete_file_from_supabase(file_path, bucket_name):
    """
    Delete a file from Supabase Storage.
    
    Args:
        file_path: Path to the file in the bucket
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not file_path:
        return False
    
    # Skip if it's a full URL (external file)
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return True
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            print("Supabase client not available. Cannot delete file.")
            return False
        
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
        
    except Exception as e:
        print(f"Error deleting from Supabase: {e}")
        return False


def get_public_url(file_path, bucket_name):
    """
    Get the public URL for a file from Supabase Storage.
    
    Args:
        file_path: Path to the file (from database) - should be just the filename
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        str: Public URL for the file
    """
    if not file_path:
        return None
    
    # Check if it's already a full URL
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return file_path
    
    # All files must be in Supabase - build Supabase public URL
    # Note: file_path should already be cleaned (just filename) after database migration
    try:
        supabase_url = current_app.config.get('SUPABASE_URL')
        if supabase_url:
            return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
    except RuntimeError:
        # Outside of application context
        pass
    
    # If no Supabase URL configured, return None (should not happen in production)
    return None


def get_activity_image_url(file_path):
    """Get public URL for an activity image."""
    from flask import current_app
    bucket = current_app.config.get('SUPABASE_BUCKET_ACTIVITIES', 'activities')
    return get_public_url(file_path, bucket)


def get_logo_url(file_path):
    """Get public URL for a logo image."""
    from flask import current_app
    bucket = current_app.config.get('SUPABASE_BUCKET_LOGOS', 'logos')
    return get_public_url(file_path, bucket)

