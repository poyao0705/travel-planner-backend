# Schema Contract

## Travel plan

### 1. Request

```json
// POST /plan
// Content-Type: application/json
{
  "destination": "Tokyo",
  "days": 3,
  "preferences": ["food", "shopping"],
  "budget": "medium"
}
```

### 2. Response
```json
{
  "trip_id": "uuid",
  "destination": "Tokyo",
  "days": 3,
  "itinerary": [
    {
      "day": 1,
      "date": "",
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
```