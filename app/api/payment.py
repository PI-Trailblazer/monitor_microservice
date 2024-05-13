from fastapi import APIRouter

from app.db.init_db import payments_collection

router = APIRouter()

# @router.get("/number_of_payments_by_nationality")
# def get_payments_by_nationality():
#     pipeline = [
#         {"$group": {"_id": "$nacionality", "num": {"$sum": 1}}}
#     ]

#     return list(payments_collection.aggregate(pipeline))
