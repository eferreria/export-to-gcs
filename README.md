# Looker Action: Export to GCS
## Introduction
Looker can send or share data using [Looker Actions](https://cloud.google.com/looker/docs/action-hub). This repository aims to showcase a workflow to serve as a proof of concept. The workflow will do the following:

1. Produce a Looker Exported file (CSV) from a Looker Object (Dashboard or Look)
2. Import the file to GCS, adding Customer Supplied Keys
3. Publish a message to a PubSub Topic

In order to create this custom data function, we will be utilizing Google Cloud Function

## Why Cloud Functions?
Cloud Functions are no-ops and a fully scalable service. Developers can create these and require little to no networking/SRE knowledge. The Cloud Function spins up based on events, in our case, a post from Looker. They can scale up to 3000 concurrent functions or scale down to zero when they are not in use which means you only pay for what you use. Cloud Functions also provide full logging capabilities and can be managed with traditional IAM settings. .

For more information, feel free to try out the Cloud Functions Qwicklab found [here](https://www.cloudskillsboost.google/focuses/916?parent=catalog).

We are going to use three Google Cloud Functions to launch our action.

In this example, we will use two separate cloud functions for our workflow, but you can use a single function and create multiple call back endpoints.

For this example, please see this [repo](https://github.com/eric-lyons/tabby/blob/main/README.md). This is the "Tabby" repo created by Eric Lyons. I have added additional functionality to publish message to PubSub and file encryption but all the inner workings have been derived from his work. Some of the instructions in Tabby have been repurposed here, with Eric's blessings.

## The Three Cloud Functions:
These names can be changed, but these three server integral parts of the action workflow.

Now, we can create our cloud functions. I choose generation 1, but feel free to customize your setup. I also selected to allow unauthorized access for ease of use and the fact we are using a token adds an extra layer of security. I picked 1 GB of memory, but this will increase your bill. The memory does depend on the complexity of your function, but please test this on your own.

Finally, I selected Python 3.8 as the runtime.

Be sure to name your entry_point the same as your controller functions. The entry_point is how programming functions are called within the Cloud function.

The 3 CFs are:
* action_list -  This serves as your "Custom Looker Action Hub" and should list all the actions you are creating
* action_form - For each action, this CF serves as the input form that can be used by the execute function
* action_execute - For each action, this CF serves as the program that executes the action that takes thes input from action_form

NOTE: If you wish to have a second custom action, you can list this in action_list as a second option, but it will need it's own action_form and action_execute

Each Cloud Function will need the minimum settings:
* HTTP Trigger type (uncheck Require HTTPS box)
* Runtime: I went with default settings (256MB, 60s timeout)
* Service Account that has Cloud Functions permissions, PubSub permissions, Storage permissions - please adhere to minimal permissions required with your use case. 
* See next section for Security section

## Creating the Authentication Mechanism
To create our token we will use openssl. I used the openssl rand -base64 32 command.

We then add this to [Google Cloud’s Secret Manager](https://cloud.google.com/secret-manager).

The first Python function used in all the action_form and action_list is the authentication function. This function checks the header added in Looker and compares it to the secret stored in the Google Cloud’s Secret Manager. If they do not match we fail the authentication and the action will fail to complete. We talk about this in a later section, but this secret is added in the Looker UI in admin --> actions. For this example, we called the token "header". When creating the Cloud Function click Security settings and reference secret. Then, select the correct key stored in Google Cloud Secret Manager. Select Exposed as Enviromental Variable. You should also follow this process in the action_execute function, where you need to reference the project_name, the email_address for the sender and the email address password. You can access these as enviromental variables with os.environ.get('NAME').

In the other functions, we checked to make sure the authentication function worked as expected and returned a 200.

```
def authenticate(request):
    if request.method != 'POST':
        r =  '|ERROR| Request must be POST'; print (r)
        return Response(r, status=401, mimetype='application/json')

    elif 'authorization' not in request.headers:
        r = '|ERROR| Request does not have auth token'; print (r)
        return Response(r, status=400, mimetype='application/json')

    else:
        # header is the name of the secret saved in Cloud Secret Manager
        expected_auth_header = 'Token token="{}"'.format(os.environ.get('header'))
        submitted_auth = request.headers['authorization']
        if hmac.compare_digest(expected_auth_header,submitted_auth):
            return Response(status=200, mimetype='application/json')

        else:
            r = '|ERROR| Incorrect token'; print (r)

```
## Files and Requirements File
Skip ahead if you are very familiar with Cloud Functions and how it works. This section will walkthru some settings that may not be super intuitive for beginners.

### Runtime and Entry Point
After indicating the secret and clicking next, you can start writing code or copy the code from each of the file presented in this repo. All of the CFs used will be using Python 3.8 for runtime. It will also ask what is the entry point. This will be the function, in my case, that will be executed at invocation. I will list the entry point in each of the CF below

For the sake of simplicity, we are using the same requirements file in each CF. The requirements.txt is the library needed typically in the python import statements. For this workflow, we needed to augment Tabby to add the library for PubSub messages so I added `google-cloud-pubsub`. Here is what I ended up having on my requirements.txt
```
# Function dependencies, for example:
# package>=version
google-cloud-storage
google-cloud-pubsub
aiohttp==3.6.2
async-timeout==3.0.1
attrs==19.3.0
cachetools==4.1.1
certifi==2020.6.20
chardet==3.0.4
click==7.1.2
Flask==1.1.2
google-api-core==1.21.0
google-api-python-client==1.10.0
google-auth==1.19.2
google-auth-httplib2==0.0.4
google-cloud-core==1.3.0
google-cloud-trace==0.23.0
googleapis-common-protos==1.52.0
grpcio==1.30.0
httplib2==0.18.1
idna==2.9
itsdangerous==1.1.0
Jinja2==2.11.2
MarkupSafe==1.1.1
multidict==4.7.6
opencensus==0.7.9
opencensus-context==0.1.1
pip==20.1.1
protobuf==3.12.2
pyasn1==0.4.8
pyasn1-modules==0.2.8
pytz==2020.1
PyYAML==5.3.1
requests==2.24.0
rsa==4.6
setuptools==47.3.1
six==1.15.0
uritemplate==3.0.1
urllib3==1.25.9
Werkzeug==1.0.1
wheel==0.34.2
wrapt==1.12.1
yarl==1.5.1
pandas==1.3.5
XlsxWriter==1.3.7
yagmail==0.15.277
```
Note that some of these may not be required, and this is not the bare minimum to run the code

### main.py
Copy the code for each cloud function into their respective main.py

## action_form
Entry Point: action_form
In action_form we defined a function called, you guessed it, action_form. It accepts the json payload as an argument. We define a response here which is the form fields users see in the Looker UI, when they select the action.
```
def action_form(request):
   auth = authenticate(request)
   if auth.status_code != 200:
       return auth

   response = [
 {"name": "bucket", "label": "GCS Bucket Name", "type": "string"},
 {"name": "subject_name", "label": "Subject Name", "type": "string"},
 {"name": "email", "label": " email address", "type": "string"}
     ]

   print ('returning form json')
   return json.dumps(response)
```
The only thing the form needs to do is return the response as JSON is the authentication function returns a 200.

## action_execute
Entry Point: buckets
The second cloud function we create is called action_execute. This is the meat and potatoes of Looker Actions. It is where we do the heavy lifting. Here we define a function called execute and set that as our entry point. We call the other functions from execute. Execute accepts response as an arg. From here, you can define your own functions, using whichever Python Libraries you would like. We can transform the data from Looker and send it to another destination.

I develop these locally and use pip freeze to show all the package versions needed for the requirements.txt file.

For further reading on the requirements.txt file, please see this link.

In our example, we created a function called email using the yagamail library to send our end user the payload. We are again using the Google Secret Manager to store the application password to the email. I would suggest using a production grade SMTP service such as SendGrid or Sailthru.

## action_list
Entry Point: action_list
Our last cloud function is action_list. Here we define a function called, action_complete and reuse the authentication function from action_form. The entry point is again set to action_complete.

The main purpose of this function is to return a response when called by the Looker action API. We define the action name, we add the URI of our icon, we define the supported action types, supported formats, and specify the form_url and url. The form_url points at the trigger for action_form which we saved in a txt file in the earlier steps and the url points to the trigger for the action_execute function which we just defined.

To create the URI we used this [open-source tool](https://onlinepngtools.com/convert-png-to-data-uri).
```
def action_list(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth
    """Return a list of actions"""
    return {
       "label": "Send Tabbed Dashboards with Tabby!",
       "integrations": [
           {
           "name": "Tabby",
           "label": "Tabby",
           "description": "Write dashboard tiles to a tabbed excel sheet.",
           "form_url":"https:FUNCTIONURLGOESHERE/action_form",
           "supported_action_types": ["dashboard"],
           "supported_download_settings": ["url"],
           "supported_formats": ["csv_zip"],
           "supported_formattings": ["unformatted"],
           "url": "https:FUNCTIONURLGOESHERE/action_execute",
           "icon_data_uri": URIGOESHERE"

           }
       ]
    }
```

## Publishing Message to PubSub Topic
Before continuing, I would advise to make sure the above works and that the minimum functionality is that the CFs will export the file into a GCS bucket after aggregating all the CSV files into a single tabbed XLS file. You will need to also make sure you configure the bucket so it can be reached by the SA and whichever application/user needs to access the exported files. 

An additional request for this workflow is to add the ability to publish messages to a pubsub topic. We will be using the [PubSub Documentation](https://cloud.google.com/pubsub/docs/publisher) in this example. I have added `google-cloud-pubsub` as part of the requirements file. I have created a separate function to publish messages, this will take an input to allow more flexibility
```
def post_to_topic(message):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    print(topic_path)
    data_str = f"{message}"

    # Data must be a bytestring
    data = data_str.encode("utf-8")
    
    future = publisher.publish(topic_path, data)
    print(future.result())
    return 1
```

## Adding File Encryption
For file encryption, this POC is using Customer Supplied Encryption Key. We will be using GCP's Secret Manager to store the key and add a second environment variable in the `action_execute` cloud function called `file_encryption_key`. More information regarding key encryption in GCS can be found in this [documentation](https://cloud.google.com/storage/docs/encryption/using-customer-supplied-keys#client-libraries_1)

In particular, we are simply using/refactoring the code in the documentation to add the file encryption in action_execute
```
  # Take the customer provided encyption key from secrets manager, mapped to filer_encryption_key variable for the cloud function
    base64_encryption_key = os.environ.get('file_encryption_key')

    # decode the key
    encryption_key = base64.b64decode(base64_encryption_key)
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
        full_path = folder_name + '/' + str(datetime.datetime.now()) + '_' +  file_name + '.xlsx'
        print(full_path)

        # encode the file using the key
        blob = bucket.blob(full_path, encryption_key=encryption_key)
        blob.upload_from_filename(path)
    
```

## Alternative Options
If you decide to use your own server, you will need to create url endpoints to call each of these functions. You will also need to ensure your allowlist settings allow traffic from Looker to pass through the firewall.

Alternatively, if you create your own action, you can attempt to submit a request to the main looker actions repo to have the action enabled on the Looker Action Hub infrastructure. While this allows other Looker customers to leverage your action, it does remove your ability to control the network settings and scale of the instances the action(s) run on.

## Adding the Action to Looker
To add the action in Looker, an admin needs to go to Admin → Actions. Scroll to the bottom of the page and select Add Action Hub. Add the action url which you can find by selecting the action_execute Cloud Function and selecting trigger. Once the url is added, then add the secret generated in the earlier section. Save these settings!

## Testing the Action with Beeceptor
[Beeceptor](https://beeceptor.com/) is a tool to intercept API calls and inspect the object. It is a free service. Feel free to use another resource if there is a preferred method.

To test the payload sent from Looker to our Cloud Function, we replace the url parameter in action_complete with the Beeceptor link. This will send the expected payload to Beecepter where we can inspect the shape and contents. This is key to customizing the action_execute function. It also allows us to understand how the parameters from the action_form object are passed over in the final payload format.

You can also use this payload in the Cloud Function testing functionality to manually pass in the payload rather than have to resent it through Looker. This is extremely useful if the query runtime for the desired schedules take a long time or is resource intensive.

## More Resources:
https://github.com/davidtamaki/looker-custom-action-content-manager

https://docs.looker.com/sharing-and-publishing/action-hub

https://training.looker.com/the-action-hub

https://github.com/looker-open-source/actions

https://github.com/looker-open-source/actions/blob/master/docs/action_api.md



