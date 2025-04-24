from datetime import datetime

def get_current_datetime_str():
    """Return current date and time in ISO format"""
    return datetime.now().isoformat() 