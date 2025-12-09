from app import create_app

flask_app = create_app()

# Note: Supabase client is automatically created with fresh config when first used
# The client detects config changes automatically, so no manual reset is needed

if __name__ == "__main__":
    flask_app.run(debug=True)