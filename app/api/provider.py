import json
import math
from datetime import datetime, timedelta

from bson import json_util
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Security

from app.api import auth_deps
from app.api.google_trends import (get_slope_and_b_of_trend_last_3_days,
                                   get_slope_and_b_of_trend_last_3_months)
from app.db.init_db import offers_collection, payments_collection

router = APIRouter()

# payments endpoints

# returns all payments from the provider's offers
@router.get("/payments")
def get_payments(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$project": {"offer": 0}}
    ]

    payments = list(payments_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(payments))

# returns the number of payments by nacitonality
@router.get("/number_of_payments_by_nationality")
def get_number_of_payments_by_nationality(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$group": {"_id": "$nationality", "num": {"$sum": 1}}}
    ]

    payments = list(payments_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(payments))

# returns the acumulated profit since the beginning of the month for the provider
@router.get("/profit_this_month")
def get_profit_this_month(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year, now.month, 1)}}},
        {"$group": {"_id": None, "profit": {"$sum": "$amount"}}},
        {"$project": {"_id": 0}}
    ]

    results = list(payments_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(results))

# returns the comparison of the profit of the current month with the previous month
@router.get("/profit_comparison_with_previous_month")
def get_profit_comparison_with_previous_month(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub
    now = datetime.now()
    last_month = now - relativedelta(months=1)

    pipeline_this_month = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year, now.month, 1)}}},
        {"$group": {"_id": None, "profit": {"$sum": "$amount"}}}
    ]

    pipeline_last_month = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(last_month.year, last_month.month, 1), "$lt": datetime(now.year, now.month, 1)}}},
        {"$group": {"_id": None, "profit": {"$sum": "$amount"}}}
    ]

    result_this_month = list(payments_collection.aggregate(pipeline_this_month))
    result_last_month = list(payments_collection.aggregate(pipeline_last_month))

    profit_this_month = result_this_month[0]['profit'] if result_this_month else 0
    profit_last_month = result_last_month[0]['profit'] if result_last_month else 0

    return profit_this_month - profit_last_month

# returns the number of sales since the beginning of the month
@router.get("/number_of_sales_this_month")
def get_number_of_sales_this_month(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub
    now = datetime.now()
    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year, now.month, 1)}}},
        {"$count": "total"}
    ]

    results = payments_collection.aggregate(pipeline)
    return json.loads(json_util.dumps(results))

# returns the comparison of the number of sales of the current month with the previous month
@router.get("/number_of_sales_comparison_with_previous_month")
def get_number_of_sales_comparison_with_previous_month(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub
    now = datetime.now()
    last_month = now - relativedelta(months=1)

    pipeline_this_month = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year, now.month, 1)}}},
        {"$count": "total"}
    ]

    pipeline_last_month = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"}},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(last_month.year, last_month.month, 1), "$lt": datetime(now.year, now.month, 1)}}},
        {"$count": "total"}
    ]

    result_this_month = list(payments_collection.aggregate(pipeline_this_month))
    result_last_month = list(payments_collection.aggregate(pipeline_last_month))

    count_this_month = result_this_month[0]['total'] if result_this_month else 0
    count_last_month = result_last_month[0]['total'] if result_last_month else 0

    return count_this_month - count_last_month

# returns the 2 more consumed tags of offers
@router.get("/most_consumed_tags")
def get_most_consumed_tags(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$unwind": "$offer"},
        {"$unwind": "$offer.tags"},
        {"$group": {"_id": "$offer.tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 2}
    ]

    results = list(payments_collection.aggregate(pipeline))

    return [doc['_id'] for doc in results]

# returns the 5 last payments
@router.get("/last_payments")
def get_last_payments(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 5},
        {"$project": {"offer": 0}}
    ]

    results = list(payments_collection.aggregate(pipeline))
    return json.loads(json_util.dumps(results))

# offers endpoints

# returns the number of offers of the provider
@router.get("/number_of_offers")
def get_number_of_offers_of_provider(payload=Security(auth_deps.verify_token, scopes=["provider"])):
    uid = payload.sub

    pipeline = [
        {"$match": {"userid": uid}},
        {"$count": "total"}
    ]

    results = list(offers_collection.aggregate(pipeline))

    return results[0]['total'] if results else 0


# graphical analysis functions and endpoint of offers and payments

# returns the number of payments by month in the last 12 months
def get_num_payments_by_month(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year - 1, now.month, 1)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "date": {"$dateToString": {"format": "%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$project": {"offer": 0}},
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
def get_num_payments_by_day(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$project": {"offer": 0}},
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
def get_num_payments_by_hour(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(hours=24)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y %H:00", "date": "$timestamp"}}}, "count": {"$sum": 1}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
        {"$project": {"offer": 0}},
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
def get_profit_by_month(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime(now.year - 1, now.month, 1)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "date": {"$dateToString": {"format": "%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$project": {"offer": 0}},
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
def get_profit_by_day(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
        {"$project": {"offer": 0}},
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
def get_profit_by_hour(uid: str):
    now = datetime.now()

    pipeline = [
        {"$lookup": {
            "from": "offers",
            "localField": "offer_id",
            "foreignField": "id",
            "as": "offer"
        }},
        {"$match": {"offer.userid": uid}},
        {"$addFields": {"timestamp": {"$toDate": "$timestamp"}}},
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(hours=24)}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}, "date": {"$dateToString": {"format": "%d/%m/%Y %H:00", "date": "$timestamp"}}}, "count": {"$sum": "$amount"}}},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}},
        {"$project": {"offer": 0}},
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
    ('month', 'num_payments'): get_num_payments_by_month,
    ('day', 'num_payments'): get_num_payments_by_day,
    ('hour', 'num_payments'): get_num_payments_by_hour,
    ('month', 'profit'): get_profit_by_month,
    ('day', 'profit'): get_profit_by_day,
    ('hour', 'profit'): get_profit_by_hour
}

@router.get("/analysis")
def get_analysis_data(x: str, y: str, payload=Security(auth_deps.verify_token, scopes=["provider"])):
    try:
        uid = payload.sub
        function_to_call = function_map[(x, y)]
        return function_to_call(uid)
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid x or y value")
    

# returns predicted values
def get_prediction(our_data_function, dates, trend_avg_slope, trend_avg_b):
    results = our_data_function()
    values = [result['count'] for result in results]

    # Calculate the 2 last slopes
    slope1 = values[-2] - values[-3]
    slope2 = values[-1] - values[-2]

    b1 = values[-3]
    b2 = - slope2 + values[-2]

    # Calculate the average slope and b
    average_slope = (slope1 + slope2) / 2
    average_b = (b1 + b2) / 2

    # Predict the number of payments for the next 3 months
    predicted_values = []

    for i in range(3, 6):
        if (trend_avg_slope * i + trend_avg_b) > 0:
            predict = (average_slope * i + average_b) + math.log(trend_avg_slope * i + trend_avg_b)
        else:
            predict = (average_slope * i + average_b) - math.log(abs(trend_avg_slope * i + trend_avg_b))
        predicted_values.append(predict)
    
    results = [{"date": date, "count": value} for date, value in zip(dates, predicted_values)]

    return json.loads(json_util.dumps(results))

@router.get("/prediction")
def get_prediction_data(x: str, y: str, payload=Security(auth_deps.verify_token, scopes=["provider"])):
    try:
        uid = payload.sub
        function_to_call = function_map[(x, y)]
        our_data_function = lambda: function_to_call(uid)
        if x == "month":
            dates = [(datetime.now() + relativedelta(months=i)).strftime("%m/%Y") for i in range(1, 4)]            
            trend_avg_slope, trend_avg_b = get_slope_and_b_of_trend_last_3_months("Aveiro")     # needs to be changed (or not)
        else:
            dates = [(datetime.now() + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(1, 4)]
            trend_avg_slope, trend_avg_b = get_slope_and_b_of_trend_last_3_days("Aveiro")       # needs to be changed (or not)
        
        return get_prediction(our_data_function, dates, trend_avg_slope, trend_avg_b)
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid x or y value")