import requests
import json
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Replace with your Elasticsearch URL
elasticsearch_url = "http://localhost:9200"

# Replace with the Elasticsearch index pattern you want to search
index_pattern = "filebeat-*"

# Replace with the Hive API URL and your Hive credentials
hive_url = "https://192.168.11.133:9000/api/v1/alert"
hive_username = "houssam@thehive.local"
hive_password = "123azert"

# Elasticsearch query
query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"agent.hostname": "akabigsmokee"}},
                {"match": {"event.kind": "alert"}}
            ]
        }
    }
}

# Function to send the alert to the Hive API
def send_alert_to_hive(alert_data):
    auth = (hive_username, hive_password)
    headers = {"Content-Type": "application/json"}

    # Extract data from Elasticsearch response and format it for TheHive
    # Adjust the fields as needed based on your data structure
    for hit in alert_data["hits"]["hits"]:
        source = hit["_source"]
        event_type = source["suricata"]["eve"]["event_type"]
        signature = source["suricata"]["eve"]["alert"]["signature"]
        category = source["suricata"]["eve"]["alert"]["category"]
        document_id = hit["_id"]  # Elasticsearch document _id

        hive_data = {
            "type": event_type,
            "source": "suricata",
            "sourceRef": document_id,  # Use Elasticsearch document _id as sourceRef
            "title": signature,
            "description": category,
            # Add other relevant fields as needed
        }

        print("Sending data to TheHive:")
        print(hive_data)

        response = requests.post(
            hive_url,
            headers=headers,
            auth=auth,
            json=hive_data,
            verify=False,  # Ignore SSL certificate verification (for testing only)
        )

        if response.status_code == 201:
            print("Alert sent to TheHive successfully!")
        else:
            print(f"Failed to send the alert to the Hive. Status code: {response.status_code}")
            print(response.text)

# Main loop to continuously run the code
while True:
    try:
        # Elasticsearch request URL
        url = f"{elasticsearch_url}/{index_pattern}/_search"

        # Perform the Elasticsearch query
        response = requests.post(url, json=query)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Send the alert to the Hive API
            send_alert_to_hive(data)
        else:
            print(f"Failed to query Elasticsearch. Status code: {response.status_code}")
            print(response.text)

        # Add a delay of 1 minute before the next iteration
        time.sleep(60)
