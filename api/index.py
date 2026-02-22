import os
import sys

# Agregamos la carpeta backend al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.main import app

# Vercel Serverless Function entrypoint
# The app object needs to be available here

# Ensure app is properly exposed for vercel
app = app
