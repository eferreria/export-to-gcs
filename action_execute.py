# Copyright 2023 Google. 
# This software is provided as-is, without warranty or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google. 

# NOTE that this is going to be in your main.py
# please supply your GCS Project ID and PubSub Topic ID
from google.cloud import storage
from google.cloud import exceptions
from google.cloud import pubsub_v1
import base64
import tempfile
import pandas as pd
import zlib
import os
import io, zipfile, json, pprint
from pandas import ExcelWriter
import tempfile
import datetime
# import yagmail


# enter project name or set it as an enviromental variable. 
tmpdir = tempfile.gettempdir()
storage_client = storage.Client(project=os.environ.get('YOUR_PROJECT_ID')) #add your ProjectID here
project_id = "YOUR_PROJECT_ID"
topic_id = "YOUR_PUBSUB_TOPIC_ID"

def buckets(request):
    request_json = request.get_json()
    convertname(request_json)
    return request_json

def upload_bucket(request_json, path):  
    folder_name = str(request_json["scheduled_plan"]['scheduled_plan_id']) + "_" + str(request_json["scheduled_plan"]['title'])
    file_name = str(request_json["scheduled_plan"]['title'])
    bucket_name = str(request_json["form_params"]["bucket"])
    # project_id = str(request_json["form_params"]["project"])
    # topic_id = str(request_json["form_params"]["topic"])
    # storage_client = storage.Client(project=os.environ.get(project_id))

    print(bucket_name)
    print(topic_id)
    print(project_id)

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
    
    except exceptions.GoogleCloudError as exception:
        bucket = None
        print("Bucket not found")
    
        return bucket

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

def convertname(request_json):
    with tempfile.TemporaryDirectory() as td:
        # EPHERMAL
        temp = tempfile.gettempdir()
        cur = os.path.join(td, "output.zip")
        with open(cur, 'wb') as result:
            result.write(base64.b64decode(request_json["attachment"]['data']))
            print(os.listdir(path=td))
        zip_ref = zipfile.ZipFile(cur, 'r')
        zip_ref.extractall(td)
        zip_ref.close()
        folder = os.listdir(td)
        file_path = os.path.join(td + '/' + folder[1])
        files = os.listdir(file_path)
        writer = pd.ExcelWriter(td + '/tabbed.xlsx', engine='xlsxwriter')

        for f in files:
            file_f = os.path.join(file_path, f)
            print(file_f)
            df = pd.read_csv(file_f)
            df.to_excel(writer, sheet_name=f, index=False)
        path = td + '/tabbed.xlsx'
        writer.save()
        message = "Uploading dashboard..."
        publish_status = post_to_topic(message)

        try:
            upload_bucket(request_json, path)
            message = "Upload complete!"
            print(message)
            publish_status = post_to_topic(message)
            print("Status: 200")
        
        except exceptions.GoogleCloudError as exception:
            message = "Error Uploading to Bucket"
            print(message)
            publish_status = post_to_topic(message)
        
        return folder
