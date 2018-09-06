# RESTful API #
Lucky CAT offers several RESTful endpoints that allow the easy integration and automation of it. This document gives an overview
of the implemented endpoints.

## Testing the RESTful API with requests ##
To quickly start with the API, use [requests](http://docs.python-requests.org). First, you have to acquire an authentication token.
```python
import requests
import json
url = "http://localhost:5000/login"
r = requests.post(url,
                  data=json.dumps({'email': 'donald@great.again', 'password': 'password'}),
                  headers={'content-type': 'application/json'})
j = r.json()
token = j['response']['user']['authentication_token']
```
Afterwards, you can send your requests, e.g. listing the current jobs:
```python
url = "http://localhost:5000/api/jobs"
r = requests.get(url, 
                 headers={'Authentication-Token': token, 
                 'content-type': 'application/json'})
print(r.json())
```
## Jobs ##
There are several endpoints to create, delete and list jobs:
- /api/jobs (GET): lists the currently registered jobs
- /api/job/<job_name> (GET): lists job information for job <job_name>
- /api/job/<job_id> (DELETE): deletes the job with <job_id>
- /api/job (PUT): creates a new job

## Crashes ##

TODO

## Statistics ##

TODO
