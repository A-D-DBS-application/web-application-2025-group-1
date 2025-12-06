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
    if _supabase_client is None:
        try:
            from supabase import create_client
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            if url and key:
                _supabase_client = create_client(url, key)
        except ImportError:
            print("Warning: supabase package not installed. Using local storage.")
        except Exception as e:
            print(f"Warning: Could not initialize Supabase client: {e}")
    return _supabase_client


def upload_file_to_supabase(file, bucket_name, folder=""):
    """
    Upload a file to Supabase Storage.
    
    Args:
        file: FileStorage object from Flask request
        bucket_name: Name of the Supabase storage bucket
        folder: Optional folder path within the bucket
    
    Returns:
        tuple: (success: bool, file_path: str or error_message: str)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    try:
        supabase = get_supabase_client()
        
        if supabase is None:
            # Fallback to local storage if Supabase is not available
            return upload_file_locally(file, bucket_name, folder)
        
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
        print(f"Error uploading to Supabase: {e}")
        # Fallback to local storage
        file.seek(0)  # Reset file pointer
        return upload_file_locally(file, bucket_name, folder)


def upload_file_locally(file, bucket_name, folder=""):
    """
    Fallback: Upload file to local static folder.
    
    Args:
        file: FileStorage object from Flask request
        bucket_name: Used as subfolder name
        folder: Optional additional folder path
    
    Returns:
        tuple: (success: bool, file_path: str or error_message: str)
    """
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{original_filename}"
        
        # Build local path
        if folder:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', bucket_name, folder)
            relative_path = f"uploads/{bucket_name}/{folder}/{unique_filename}"
        else:
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', bucket_name)
            relative_path = f"uploads/{bucket_name}/{unique_filename}"
        
        # Create directory if needed
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return relative path with LOCAL: prefix to indicate local storage
        return True, f"LOCAL:{relative_path}"
        
    except Exception as e:
        return False, f"Error saving file locally: {e}"


def delete_file_from_supabase(file_path, bucket_name):
    """
    Delete a file from Supabase Storage.
    
    Args:
        file_path: Path to the file in the bucket
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        if supabase is None or file_path.startswith("LOCAL:"):
            # Delete locally if Supabase not available or file is local
            return delete_file_locally(file_path)
        
        supabase.storage.from_(bucket_name).remove([file_path])
        return True
        
    except Exception as e:
        print(f"Error deleting from Supabase: {e}")
        return False


def delete_file_locally(file_path):
    """
    Delete a file from local storage.
    
    Args:
        file_path: Path to the file (may have LOCAL: prefix)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Remove LOCAL: prefix if present
        if file_path.startswith("LOCAL:"):
            file_path = file_path[6:]
        
        full_path = os.path.join(current_app.root_path, 'static', file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        return True
        
    except Exception as e:
        print(f"Error deleting local file: {e}")
        return False


def get_public_url(file_path, bucket_name):
    """
    Get the public URL for a file.
    
    Args:
        file_path: Path to the file (from database)
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        str: Public URL for the file
    """
    if not file_path:
        return None
    
    # Check if it's a local file
    if file_path.startswith("LOCAL:"):
        # Return Flask static URL path
        local_path = file_path[6:]  # Remove "LOCAL:" prefix
        return f"/static/{local_path}"
    
    # Check if it's an old-style local path (backwards compatibility)
    if file_path.startswith("uploads/"):
        return f"/static/{file_path}"
    
    # Check if it's already a full URL
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return file_path
    
    # Build Supabase public URL
    try:
        supabase_url = current_app.config.get('SUPABASE_URL')
        if supabase_url:
            return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
    except RuntimeError:
        # Outside of application context
        pass
    
    # Fallback: assume it's a local path
    return f"/static/{file_path}"


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

