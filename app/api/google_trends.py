from serpapi import GoogleSearch
from app.core.config import settings


def get_trends(seacrh_term: str):
    params = {
        "engine": "google_trends",
        "q": seacrh_term,
        "cat": "208",
        "api_key": settings.GOOGLE_TRENDS_API_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results


def get_difference_between_recent_and_old_values():
    trends = get_trends()
    values = trends["interest_over_time"]["timeline_data"]

    recent_value = values[-1]["values"][0]["extracted_value"]
    old_value = values[0]["values"][0]["extracted_value"]

    return recent_value - old_value
