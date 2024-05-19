import json
from datetime import datetime, timedelta

from bson import json_util
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException

from app.db.init_db import offers_collection, payments_collection

router = APIRouter()

# payments endpoints

# returns the number of payments by nationality
@router.get("/number_of_payments_by_nationality")
def get_payments_by_nationality():
    pipeline = [
        {"$group": {"_id": "$nationality", "num": {"$sum": 1}}}
    ]

    return list(payments_collection.aggregate(pipeline))

# returns all payments
@router.get("/payments/")
def get_payments():
    payments = list(payments_collection.find())
    return json.loads(json_util.dumps(payments))


# offers endpoints

# returns the total number of offers
@router.get("/total_number_of_offers")
def get_total_number_of_offers():
    pipeline = [
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$count": "total"}
    ]

    results = list(offers_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(results))

# returns the variation of the total number of offers compared to the previous month
@router.get("/total_number_of_offers_variation_since_30_days_ago")
async def get_total_number_of_offers_variation_since_30_days_ago():
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)

    pipeline_today = [
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$count": "total"}
    ]

    pipeline_30_days_ago = [
        {"$match": {"timestamp": {"$lt": thirty_days_ago}}},
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$count": "total"}
    ]

    result_today = list(offers_collection.aggregate(pipeline_today))
    result_last_month = list(offers_collection.aggregate(pipeline_30_days_ago))

    count_today = result_today[0]['total'] if result_today else 0
    count_last_month = result_last_month[0]['total'] if result_last_month else 0

    return count_today - count_last_month

# returns the number of offers by tag
@router.get("/number_of_offers_by_tag")
def get_offers_by_tag():
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$sort": {"timestamp": -1}},
        {"$group": {"_id": "$id", "tags": {"$first": "$tags"}}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "num": {"$sum": 1}}}
    ]

    return list(offers_collection.aggregate(pipeline))

# returns all offers
@router.get("/offers/")
def get_offers():
    offers = list(offers_collection.find())
    return json.loads(json_util.dumps(offers))


# graphical analysis functions and endpoint of offers and payments

# returns the total number of offers variation by month in the last 12 months
# @router.get("/total_number_of_offers_by_month")
def get_total_number_of_offers_by_month():
    now = datetime.now()
    results = []

    for i in range(-1, 11):
        month_ago = now - relativedelta(months=i)
        pipeline = [
            {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
            {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
            {"$match": {"timestamp": {"$lt": datetime(month_ago.year, month_ago.month, 1)}}},
            {"$count": "total"}
        ]

        result = list(offers_collection.aggregate(pipeline))

        if result:
            results.append({"count": result[0]['total'], "date": (month_ago - relativedelta(months=1)).strftime('%m/%Y')})
        else:
            results.append({"count": 0, "date": (month_ago - relativedelta(months=1)).strftime('%m/%Y')})
        
        # Sort the results by date
        results.sort(key=lambda result: datetime.strptime(result['date'], "%m/%Y"))
    
    return results

# returns the total number of offers variation by day in the last 30 days
# @router.get("/total_number_of_offers_by_day")
def get_total_number_of_offers_by_day():
    now = datetime.now()
    results = []

    for i in range(-1, 29):
        day_ago = now - timedelta(days=i)
        pipeline = [
            {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
            {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
            {"$match": {"timestamp": {"$lt": datetime(day_ago.year, day_ago.month, day_ago.day)}}},
            {"$count": "total"}
        ]

        result = list(offers_collection.aggregate(pipeline))

        if result:
            results.append({"count": result[0]['total'], "date": (day_ago - relativedelta(days=1)).strftime('%d/%m/%Y')})
        else:
            results.append({"count": 0, "date": (day_ago - relativedelta(days=1)).strftime('%d/%m/%Y')})
        
        # Sort the results by date
        results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y"))
    
    return results

# returns the total number of offers variation by hour in the last 24 hours
# @router.get("/total_number_of_offers_by_hour")
def get_total_number_of_offers_by_hour():
    now = datetime.now()
    results = []

    for i in range(24):
        hour_ago = now - timedelta(hours=i)
        pipeline = [
            {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
            {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
            {"$match": {"timestamp": {"$lt": datetime(hour_ago.year, hour_ago.month, hour_ago.day, (hour_ago+timedelta(hours=1)).hour)}}},
            {"$count": "total"}
        ]

        result = list(offers_collection.aggregate(pipeline))

        if result:
            results.append({"count": result[0]['total'], "date": hour_ago.strftime('%d/%m/%Y %H:00')})
        else:
            results.append({"count": 0, "date": hour_ago.strftime('%d/%m/%Y %H:00')})

        # Sort the results by date
        results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y %H:%M"))

    return results

# returns the number of new offers by month in the last 12 months
# @router.get("/new_offers_by_month")
def get_new_offers_by_month():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year - 1, now.month, 1)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "date": {"$dateToString": {"format": "%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(offers_collection.aggregate(pipeline))

    # Create a list of all months in the last 12 months
    all_months = [(now - timedelta(days=30*i)).strftime('%m/%Y') for i in range(12)]

    # Merge the list of all months with the results
    for month in all_months:
        if not any(result['date'] == month for result in results):
            results.append({'count': 0, 'date': month})
    
    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the number of new offers by day in the last 30 days
# @router.get("/new_offers_by_day")
def get_new_offers_by_day():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(offers_collection.aggregate(pipeline))

    # Create a list of all days in the last 30 days
    all_days = [(now - timedelta(days=i)).strftime('%d/%m/%Y') for i in range(30)]

    # Merge the list of all days with the results
    for day in all_days:
        if not any(result['date'] == day for result in results):
            results.append({'count': 0, 'date': day})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the number of new offers by hour in the last 24 hours
# @router.get("/new_offers_by_hour")
def get_new_offers_by_hour():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$group": {"_id": "$id", "timestamp": {"$min": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(hours=24)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y %H:00", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(offers_collection.aggregate(pipeline))

    # Create a list of all hours in the day
    all_hours = [(now - timedelta(hours=i)).strftime('%d/%m/%Y %H:00') for i in range(24)]

    # Merge the list of all hours with the results
    for hour in all_hours:
        if not any(result['date'] == hour for result in results):
            results.append({'count': 0, 'date': hour})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y %H:%M"))

    return json.loads(json_util.dumps(results))

# returns the number of payments by month in the last 12 months
def get_num_payments_by_month():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year - 1, now.month, 1)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "date": {"$dateToString": {"format": "%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all months in the last 12 months
    all_months = [(now - timedelta(days=30*i)).strftime('%m/%Y') for i in range(12)]

    # Merge the list of all months with the results
    for month in all_months:
        if not any(result['date'] == month for result in results):
            results.append({'count': 0, 'date': month})
    
    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the number of payments by day in the last 30 days
def get_num_payments_by_day():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all days in the last 30 days
    all_days = [(now - timedelta(days=i)).strftime('%d/%m/%Y') for i in range(30)]

    # Merge the list of all days with the results
    for day in all_days:
        if not any(result['date'] == day for result in results):
            results.append({'count': 0, 'date': day})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the number of payments by hour in the last 24 hours
def get_num_payments_by_hour():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(hours=24)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y %H:00", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all hours in the day
    all_hours = [(now - timedelta(hours=i)).strftime('%d/%m/%Y %H:00') for i in range(24)]

    # Merge the list of all hours with the results
    for hour in all_hours:
        if not any(result['date'] == hour for result in results):
            results.append({'count': 0, 'date': hour})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y %H:%M"))

    return json.loads(json_util.dumps(results))

# returns the profit by month in the last 12 months
def get_profit_by_month():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year - 1, now.month, 1)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "date": {"$dateToString": {"format": "%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all months in the last 12 months
    all_months = [(now - timedelta(days=30*i)).strftime('%m/%Y') for i in range(12)]

    # Merge the list of all months with the results
    for month in all_months:
        if not any(result['date'] == month for result in results):
            results.append({'count': 0, 'date': month})
    
    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the profit by day in the last 30 days
def get_profit_by_day():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all days in the last 30 days
    all_days = [(now - timedelta(days=i)).strftime('%d/%m/%Y') for i in range(30)]

    # Merge the list of all days with the results
    for day in all_days:
        if not any(result['date'] == day for result in results):
            results.append({'count': 0, 'date': day})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y"))

    return json.loads(json_util.dumps(results))

# returns the profit by hour in the last 24 hours
def get_profit_by_hour():
    now = datetime.now()
    pipeline = [
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(hours=24)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y %H:00", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
        {"$project": {"_id": 0, "date": "$_id.date", "count": 1}}
    ]

    results = list(payments_collection.aggregate(pipeline))

    # Create a list of all hours in the day
    all_hours = [(now - timedelta(hours=i)).strftime('%d/%m/%Y %H:00') for i in range(24)]

    # Merge the list of all hours with the results
    for hour in all_hours:
        if not any(result['date'] == hour for result in results):
            results.append({'count': 0, 'date': hour})

    # Sort the results by date
    results.sort(key=lambda result: datetime.strptime(result['date'], "%d/%m/%Y %H:%M"))

    return json.loads(json_util.dumps(results))

function_map = {
    ('total_offers', 'month'): get_total_number_of_offers_by_month,
    ('total_offers', 'day'): get_total_number_of_offers_by_day,
    ('total_offers', 'hour'): get_total_number_of_offers_by_hour,
    ('new_offers', 'month'): get_new_offers_by_month,
    ('new_offers', 'day'): get_new_offers_by_day,
    ('new_offers', 'hour'): get_new_offers_by_hour,
    ('num_payments', 'month'): get_num_payments_by_month,
    ('num_payments', 'day'): get_num_payments_by_day,
    ('num_payments', 'hour'): get_num_payments_by_hour,
    ('profit', 'month'): get_profit_by_month,
    ('profit', 'day'): get_profit_by_day,
    ('profit', 'hour'): get_profit_by_hour
}

@router.get("/analysis/")
def get_analysis_data(x: str, y: str):
    try:
        return function_map[(x, y)]()
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid x or y value")