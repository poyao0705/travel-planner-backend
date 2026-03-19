from fastapi import APIRouter

from app.api.core.log import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("")
def get_plan():
    # req = await request.json()
    logger.info("Received request")

    return {
  "trip_id": "uuid",
  "destination": "Tokyo",
  "days": 3,
  "itinerary": [
    {
      "day": 1,
      "date": "2024-06-01",
      "items": [
        {
          "id": "poi_1",
          "title": "Shibuya Crossing",
          "description": "Famous crossing",
          "location": {
            "lat": 35.6595,
            "lng": 139.7005
          },
          "start_time": "09:00",
          "end_time": "11:00",
          "type": "attraction"
        }
      ]
    }
  ]
}