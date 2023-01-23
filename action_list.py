# add this to main.py of cloud function
# replace the URLs to the trigger URLs of action_form and action_execute
import os
import hmac
from flask import Response

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
            print(expected_auth_header)
            print(submitted_auth)
            print(request)
            return Response(r, status=403, mimetype='application/json')




def action_list(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth
    """Return a list of actions"""
    return {
       "label": "Custom Looker Integrations",
       "integrations": [
           {
           "name": "ExportToGCS",
           "label": "Convert to XLS, Export to Google Cloud Storage",
           "description": "Consolidate dashboard tiles to a tabbed excel sheet in a GCS Bucket.",
           "form_url":"REPLACE_WITH_ACTION_FORM_TRIGGER_URL",
           "supported_action_types": ["dashboard"],
           "supported_download_settings": ["url"],
           "supported_formats": ["csv_zip"],
           "supported_formattings": ["unformatted"],
           "url": "REPLACE_WITH_ACTION_EXECUTE_TRIGGER_URL"       
           }
       ]
    }
