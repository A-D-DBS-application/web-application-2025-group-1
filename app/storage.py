"""
Supabase Storage utilities for uploading and managing images.
Uses anon key for authentication (requires Storage policies to be configured).
"""
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
import os

# Supabase client instance (lazy initialization with config tracking)
_supabase_client = None
_client_config_hash = None


def reset_supabase_client(silent=False):
    """Reset the Supabase client (useful when config changes).
    
    Args:
        silent: If True, don't print reset message (default: False)
    """
    global _supabase_client, _client_config_hash
    if not silent:
        print("Resetting Supabase client...")
    _supabase_client = None
    _client_config_hash = None


def get_supabase_client(force_new=False):
    """Get or create the Supabase client instance.
    
    Uses anon key from configuration. The client is cached but recreated
    if the configuration changes.
    
    Args:
        force_new: If True, force creation of new client (useful for debugging)
    
    Returns:
        Supabase client instance or None if initialization fails
    """
    global _supabase_client, _client_config_hash
    
    if force_new:
        _supabase_client = None
        _client_config_hash = None
    
    try:
        # Always try to get config values (in case they changed)
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_KEY')
        
        if not url:
            print("Error: SUPABASE_URL not found in configuration")
            _supabase_client = None
            _client_config_hash = None
            return None
        if not key:
            print("Error: SUPABASE_KEY not found in configuration")
            _supabase_client = None
            _client_config_hash = None
            return None
        
        # Clean the key: remove whitespace and newlines
        key = key.strip()
        
        # Create a hash of the current config to detect changes
        import hashlib
        config_hash = hashlib.md5(f"{url}:{key}".encode()).hexdigest()
        
        # Validate key format (JWT tokens start with eyJ)
        if not key.startswith('eyJ'):
            print("Warning: SUPABASE_KEY doesn't appear to be a valid JWT token.")
            print(f"Key preview: {key[:20]}... (first 20 chars)")
        
        # Always create a fresh client to ensure we use the latest config
        # This prevents issues with cached clients using old keys
        from supabase import create_client
        # Ensure URL doesn't have trailing slash
        url = url.rstrip('/')
        
        # Decode JWT to verify it's anon key
        role = 'unknown'
        try:
            import base64
            import json
            parts = key.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                jwt_data = json.loads(decoded)
                role = jwt_data.get('role', 'unknown')
                if role != 'anon':
                    print(f"⚠️  WARNING: Key role is '{role}', expected 'anon'!")
        except Exception as decode_err:
            pass  # Non-critical
        
        # Create new client
        try:
            client = create_client(url, key)
            
            # Only cache if config hasn't changed (for performance)
            if _supabase_client is None or _client_config_hash != config_hash:
                _supabase_client = client
                _client_config_hash = config_hash
                print(f"Supabase client initialized/reinitialized")
                print(f"  URL: {url}")
                print(f"  Key length: {len(key)} chars")
                print(f"  Key role: {role}")
            
            return client
        except ImportError as e:
            print(f"Error: supabase package not installed: {e}")
            print("Please install it with: pip install supabase")
            _supabase_client = None
            _client_config_hash = None
            return None
        except Exception as e:
            print(f"Error: Could not initialize Supabase client: {e}")
            print(f"URL: {url}")
            print(f"Key length: {len(key) if key else 0} characters")
            _supabase_client = None
            _client_config_hash = None
            return None
        
    except RuntimeError as e:
        # Outside of application context
        print(f"Error: Cannot access Flask application context: {e}")
        return None
    except Exception as e:
        print(f"Error: Unexpected error in get_supabase_client: {e}")
        return None


def upload_file_to_supabase(file, bucket_name, folder=""):
    """
    Upload a file to Supabase Storage using anon key.
    Requires Storage bucket policies to be configured for anon uploads.
    
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
    
    supabase = get_supabase_client(force_new=False)
    
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
        
        # Read file content as bytes
        file.seek(0)  # Ensure we're at the start
        file_content = file.read()
        file.seek(0)  # Reset for potential future reads
        
        # Validate file content
        if not file_content or len(file_content) == 0:
            return False, "File is empty or could not be read"
        
        # Get content type
        content_type = file.content_type or 'application/octet-stream'
        
        # Log upload attempt for debugging
        print(f"Attempting upload to bucket '{bucket_name}'")
        print(f"File path: {file_path}")
        print(f"File size: {len(file_content)} bytes")
        print(f"Content type: {content_type}")
        
        # Upload to Supabase Storage
        # For anon key, we need to ensure proper authentication
        try:
            # Try upload with explicit options
            response = supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": "true"  # Allow overwriting existing files
                }
            )
            
            # Check response - Supabase Python SDK returns different response types
            # Response can be a dict, object, or None
            if response is None:
                # Upload might have succeeded but returned None
                print(f"Upload completed (response is None) for {file_path}")
                return True, file_path
            
            # Check if response has error attribute
            if hasattr(response, 'error') and response.error:
                error_msg = f"Supabase upload error: {response.error}"
                print(error_msg)
                return False, error_msg
            
            # Check if response is a dict with error
            if isinstance(response, dict) and 'error' in response:
                error_msg = f"Supabase upload error: {response.get('error')}"
                print(error_msg)
                return False, error_msg
            
            # Check for error message in response
            if isinstance(response, dict) and response.get('error'):
                error_msg = f"Supabase upload error: {response.get('error')}"
                print(error_msg)
                return False, error_msg
            
            # If we get here, upload was successful
            print(f"Upload successful for {file_path}")
            return True, file_path
            
        except Exception as upload_error:
            # Catch upload-specific errors
            error_str = str(upload_error)
            error_repr = repr(upload_error)
            print(f"=== UPLOAD EXCEPTION ===")
            print(f"Exception type: {type(upload_error).__name__}")
            print(f"Error string: {error_str}")
            print(f"Error repr: {error_repr}")
            
            # Check if it's a Supabase API error
            if hasattr(upload_error, 'message'):
                print(f"Error message: {upload_error.message}")
            if hasattr(upload_error, 'status_code'):
                print(f"Status code: {upload_error.status_code}")
            if hasattr(upload_error, 'response'):
                print(f"Response: {upload_error.response}")
            
            raise  # Re-raise to be caught by outer exception handler
        
    except Exception as e:
        # Provide more detailed error information
        error_str = str(e)
        error_type = type(e).__name__
        
        # Log full error for debugging
        print(f"=== UPLOAD ERROR DETAILS ===")
        print(f"Error type: {error_type}")
        print(f"Error message: {error_str}")
        print(f"Bucket: {bucket_name}")
        print(f"File path: {file_path if 'file_path' in locals() else 'N/A'}")
        
        # Check Supabase client configuration
        try:
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            print(f"Supabase URL: {url}")
            print(f"Supabase Key present: {bool(key)}")
            print(f"Supabase Key length: {len(key) if key else 0}")
            print(f"Supabase Key starts with eyJ: {key.startswith('eyJ') if key else False}")
            print(f"Supabase Key preview: {key[:50] if key else 'N/A'}...")
            
            # Check if it's anon key (typically shorter, contains 'anon' in JWT payload)
            if key and key.startswith('eyJ'):
                try:
                    import base64
                    import json
                    # Decode JWT to check role
                    parts = key.split('.')
                    if len(parts) >= 2:
                        # Decode payload (second part)
                        payload = parts[1]
                        # Add padding if needed
                        padding = 4 - len(payload) % 4
                        if padding != 4:
                            payload += '=' * padding
                        decoded = base64.urlsafe_b64decode(payload)
                        jwt_data = json.loads(decoded)
                        role = jwt_data.get('role', 'unknown')
                        print(f"JWT role from key: {role}")
                        if role != 'anon':
                            print(f"⚠️  WARNING: Key role is '{role}', should be 'anon'!")
                except Exception as decode_error:
                    print(f"Could not decode JWT: {decode_error}")
        except Exception as config_error:
            print(f"Error checking config: {config_error}")
        
        # Determine error message based on error type
        if "Invalid Compact JWS" in error_str or "Unauthorized" in error_str or "403" in error_str:
            error_msg = (
                "Authentication error: Upload failed. Possible causes:\n"
                "1. SUPABASE_KEY is not the anon key (check your .env file)\n"
                "2. Storage bucket policies are not configured correctly\n"
                "3. Bucket is not set to 'public'\n\n"
                "Please verify:\n"
                "- Your SUPABASE_KEY in .env is the anon key (not service_role)\n"
                "- Storage → Policies shows INSERT policy for 'anon' role on 'activities' bucket\n"
                "- Storage → Buckets shows 'activities' bucket is PUBLIC"
            )
        elif "JWT" in error_str or "token" in error_str.lower():
            error_msg = f"JWT token error: {error_str}. Please verify your SUPABASE_KEY (anon key) is correct and properly formatted (no extra whitespace or newlines)."
        elif "new row violates row-level security policy" in error_str.lower() or "policy" in error_str.lower() or "row-level security" in error_str.lower():
            error_msg = (
                "Storage policy error: Row-level security policy violation. "
                "Please verify in Supabase Dashboard:\n"
                "1. Storage → Policies → activities bucket\n"
                "2. There should be a policy 'Allow anon uploads to activities' for INSERT operation\n"
                "3. The policy should have 'anon' in the 'Applied to' field"
            )
        elif "bucket" in error_str.lower() and ("not found" in error_str.lower() or "does not exist" in error_str.lower()):
            error_msg = f"Bucket error: The '{bucket_name}' bucket does not exist. Please create it in Supabase Dashboard → Storage → Buckets"
        else:
            error_msg = f"Error uploading to Supabase: {error_str}"
        
        print(f"=== END ERROR DETAILS ===")
        return False, error_msg


def delete_file_from_supabase(file_path, bucket_name):
    """
    Delete a file from Supabase Storage using anon key.
    
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
