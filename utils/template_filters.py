"""
Filtros personalizados para las plantillas Jinja2
"""
import pytz
from datetime import datetime

def utc_to_colombia(utc_dt):
    """Convertir datetime UTC a hora de Colombia"""
    if utc_dt is None:
        return None
    colombia_tz = pytz.timezone('America/Bogota')
    if utc_dt.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        utc_dt = pytz.UTC.localize(utc_dt)
    return utc_dt.astimezone(colombia_tz)

def register_template_filters(app):
    """Registrar filtros personalizados en la aplicación Flask"""
    app.jinja_env.filters['utc_to_colombia'] = utc_to_colombia