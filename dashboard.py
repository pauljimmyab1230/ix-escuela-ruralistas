"""Punto de entrada heredado.

Se conserva por compatibilidad con configuraciones existentes que invocan
`streamlit run dashboard.py`. La implementación vive en `app.py`.
"""

from app import main

if __name__ == "__main__":
    main()
