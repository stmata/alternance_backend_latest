#!/bin/bash

# Activer un environnement virtuel si nécessaire (par exemple, si vous utilisez un environnement virtuel personnalisé)
# source /path/to/your/virtualenv/bin/activate

# Lancer l'application FastAPI avec Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000