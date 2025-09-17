# API Specifications

## Base URL


---

## POST /allocate

Allocate resources based on the input JSON payload.

### Request

- **URL**: `/allocate`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "groups": [
    {
      "group_id": "string",
      "students": [
        {
          "name": "string",
          "student_id": "string",
          "unikey": "string",
          "unit_code": "string"
        }
      ],
      "project_preferences": ["string"],
      "wam_breakdown": {
        "HD": int,
        "D": int,
        "CR": int,
        "P": int
      },
      "dual_project_enrollment": true,
      "skills": ["string"],
      "justification": "string"
    }
  ]
}
```
### Response
#### Status 200 OK
```json
{
  "allocations": {
    "SOFT3888_TU12_03": "P07",
    "COMP3888_M10_03": "P44"
  }
}
```
#### Error (500 Internal Server Error)
```json
{
  "detail": "Error message here"
}
```

### Example

```
Terminal:
git clone https://github.sydney.edu.au/rkam0278/SOFT3888_TH08_03-P42
cd SOFT3888_TH08_03-P42/backend/
python3 -m venv venv
source venv/bin/activate
pip install -r docs/requirements.txt
python -m uvicorn app.main:app --reload
curl -X POST "http://127.0.0.1:8000/allocate" \
     -H "Content-Type: application/json" \
     -d @data/example_backend_input.json
     
Response:
{"allocations":{"SOFT3888_TU12_03":"P07","COMP3888_M10_03":"P44"}}
```
