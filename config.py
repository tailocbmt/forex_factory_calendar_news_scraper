# Local folder
FOLDER_NAME = "news"

# Drive folder
SERVICE_ACCOUNT_FILE = "secrets/credentials.json"
SHARED_FOLDER_ID = "ForexFactory"  # ForexFactory

# Constants for allowed classes and patterns
REQUEST_URL = "https://www.forexfactory.com/calendar"

MONTH_NUM_TO_NAME = {
    1: "jan",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dec"
}

ALLOWED_ELEMENT_TYPES = {
    "calendar__cell": "date",
    "calendar__cell calendar__date": "date",
    "calendar__cell calendar__time": "time",
    "calendar__cell calendar__currency": "currency",
    "calendar__cell calendar__impact": "impact",
    "calendar__cell calendar__event event": "event"
}

EXCLUDED_ELEMENT_TYPES = [
    "calendar__cell calendar__forecast",
    "calendar__cell calendar__graph",
    "calendar__cell calendar__previous"
]

ICON_COLOR_MAP = {
    "icon icon--ff-impact-yel": "Low",
    "icon icon--ff-impact-ora": "Medium",
    "icon icon--ff-impact-red": "High",
    "icon icon--ff-impact-gra": "Holiday"
}

# THE CURRENCY CODES I WANT TO SCRAPE
ALLOWED_CURRENCY_CODES = ['CAD', 'EUR', 'GBP', 'USD', 'NZD']

# THE NEWS EVENTS WITH IMPACTS, THAT I WANT TO SCRAPE
ALLOWED_IMPACT_COLORS = ['High', 'Holiday']
