import itertools
from collections import defaultdict
from datetime import datetime

from serpapi import GoogleSearch

from app.core.config import settings


def get_trends(seacrh_term: str, date: str):
    params = {
        "engine": "google_trends",
        "q": seacrh_term,
        'date': date,
        "api_key": settings.GOOGLE_TRENDS_API_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results

# def get_slope_of_trend_last_3_hours(search_term: str):
#     trends = get_trends(search_term, "now 4-H")
#     # values = trends["interest_over_time"]["timeline_data"]

#     return trends

def get_slope_and_b_of_trend_last_3_days(search_term: str):
    trends = get_trends(search_term, "today 1-m")
    values = trends["interest_over_time"]["timeline_data"]

    # Calculate the slopes and b values
    slope1 = values[-2]['values'][0]['extracted_value'] - values[-3]['values'][0]['extracted_value']

    b1 = values[-3]['values'][0]['extracted_value']

    slope2 = values[-1]['values'][0]['extracted_value'] - values[-2]['values'][0]['extracted_value']

    b2 = - slope2 + values[-2]['values'][0]['extracted_value']

    average_slope = (slope1 + slope2) / 2

    average_b = (b1 + b2) / 2

    return average_slope, average_b

def get_slope_and_b_of_trend_last_3_months(search_term: str):
    trends = get_trends(search_term, "today 3-m")
    values = trends["interest_over_time"]["timeline_data"]

    monthly_totals = defaultdict(int)
    monthly_counts = defaultdict(int)

    even_division = len(values) // 3

    first_month = values[:even_division]
    second_month = values[even_division:even_division * 2]
    third_month = values[even_division * 2:]

    for day in first_month:
        value = day['values'][0]['extracted_value']

        monthly_totals[0] += value
        monthly_counts[0] += 1

    for day in second_month:
        value = day['values'][0]['extracted_value']

        monthly_totals[1] += value
        monthly_counts[1] += 1

    for day in third_month:
        value = day['values'][0]['extracted_value']

        monthly_totals[2] += value    
        monthly_counts[2] += 1
    
    
    slopes = []
    for i in range(2):
        slope = (monthly_totals[i + 1]/monthly_counts[i + 1] - monthly_totals[i]/monthly_counts[i])
        slopes.append(slope)
    
    average_slope = sum(slopes) / 2

    b1 = monthly_totals[0]/monthly_counts[0]
    b2 = monthly_totals[1]/monthly_counts[1] - slopes[0]

    average_b = (b1 + b2) / 2

    return average_slope, average_b