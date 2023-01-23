# Copyright 2023 Google. 
# This software is provided as-is, without warranty or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google. 

# NOTE that this is going to be in your main.py
# https://github.com/looker/actions/blob/master/docs/action_api.md#action-form-endpoint
import os
import hmac
from flask import Response
import json

# https://github.com/looker/actions/blob/master/docs/action_api.md#authentication
def authenticate(request):
    if request.method != 'POST':
        r =  '|ERROR| Request must be POST'; print (r)
        return Response(r, status=401, mimetype='application/json')

    elif 'authorization' not in request.headers:
        r = '|ERROR| Request does not have auth token'; print (r)
        return Response(r, status=400, mimetype='application/json')

    else:
        expected_auth_header = 'Token token="{}"'.format(os.environ.get('header'))
        submitted_auth = request.headers['authorization']
        if hmac.compare_digest(expected_auth_header,submitted_auth):
            return Response(status=200, mimetype='application/json')

        else:
            r = '|ERROR| Incorrect token'; print (r)
            return Response(r, status=403, mimetype='application/json')



def action_form(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    response = [
  {"name": "bucket", "label": "GCS Bucket Name", "type": "string"}
  , {"name": "project", "label": "GCS Project ID", "type": "string"}
  , {"name": "topic", "label": "GCS PubSub Topic", "type": "string"}
 #, {"name": "email", "label": " email address", "type": "string"}
      ]

    print ('returning form json')
    return json.dumps(response)
