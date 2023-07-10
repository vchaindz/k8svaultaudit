import os
import json
import hashlib
import argparse
import requests
from kubernetes import client, config, watch
from datetime import datetime
from deepdiff import DeepDiff
from deepdiff.serialization import json_dumps

# Parse command line arguments
parser = argparse.ArgumentParser(description='Monitor Kubernetes configurations.')
parser.add_argument('--kubeconfig', type=str, help='Path to the kubeconfig file.')
parser.add_argument('--namespace', type=str, help='Specific namespace to monitor.')
parser.add_argument('--apikey', type=str, help='API key for the vault.immudb.io service.')
args = parser.parse_args()

# Load Kubernetes configuration file from command line argument or environment variable
kube_config_path = args.kubeconfig or os.getenv('KUBECONFIG', '/path/to/your/kubeconfig')
config.load_kube_config(kube_config_path)

# Set the namespace to watch
namespace_to_watch = args.namespace or os.getenv('NAMESPACE', None)

# Get API key for the vault.immudb.io service from command line argument or environment variable
api_key = args.apikey or os.getenv('VAULT_IMMUDB_API_KEY', None)
if not api_key:
    raise Exception('No API key provided for the vault.immudb.io service.')

v1 = client.CoreV1Api()

# Store hashes and configurations of pods
pod_data_store = {}

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

# Creating a Session to handle the requests
s = requests.Session()
s.headers.update({"Content-Type": "application/json", "X-API-KEY": api_key})

while True:
    # Get all pods
    if namespace_to_watch:
        pods = v1.list_namespaced_pod(namespace=namespace_to_watch, watch=False)
    else:
        pods = v1.list_pod_for_all_namespaces(watch=False)

    for pod in pods.items:
        # Convert pod data to JSON, handling datetime objects
        pod_data = json.loads(json.dumps(pod.to_dict(), sort_keys=True, default=datetime_handler))
        pod_data["itemtype"] = "kubernetesconfig"
        
        # Hash the JSON data
        pod_hash = hashlib.sha256(json.dumps(pod_data, sort_keys=True).encode('utf-8')).hexdigest()

        if pod.metadata.name not in pod_data_store:
            # If the pod is new, add it to the data store and send to immudb.io
            pod_data_store[pod.metadata.name] = {'hash': pod_hash, 'config': pod_data}
            inserted = s.put("https://vault.immudb.io/ics/api/v1/ledger/default/collection/default/document", 
                             json=pod_data)
            assert inserted.status_code == 200
            print(f"New configuration for pod {pod.metadata.name} has been sent to the vault")

        elif pod_data_store[pod.metadata.name]['hash'] != pod_hash:
            # If the pod configuration has changed, update the data store and send new config to immudb.io
            old_config = pod_data_store[pod.metadata.name]['config']
            new_config = pod_data
            
            # Send new configuration to immudb.io
            inserted = s.put("https://vault.immudb.io/ics/api/v1/ledger/default/collection/default/document", 
                             json=new_config)
            assert inserted.status_code == 200
            print(f"Updated configuration for pod {pod.metadata.name} has been sent to the vault")
            
            # Update the pod data store
            pod_data_store[pod.metadata.name] = {'hash': pod_hash, 'config': new_config}

            # Get the last two entries for this pod from immudb.io
            lastTwoEntries = s.post("https://vault.immudb.io/ics/api/v1/ledger/default/collection/default/documents/search", 
                                    json={
                                        "page": 0,
                                        "perPage": 2,
                                        "orderBy": [{"desc": True, "field": "_id"}],
                                        "query": {
                                            "expression": {
                                                "fieldComparisons": {
                                                    "field": "itemtype",
                                                    "operator": "EQ",
                                                    "value": "kubernetesconfig"
                                                }
                                            }
                                        }
                                    })

            # If there are no previous revisions, continue with the next pod
            if 'revisions' not in lastTwoEntries.json():
                continue
            
            firstDocument = lastTwoEntries.json()["revisions"][0]["document"]
            secondDocument = lastTwoEntries.json()["revisions"][1]["document"]

            # Use DeepDiff to find the changes between the old and new configuration
            differencer = DeepDiff(firstDocument, secondDocument, ignore_order=True, exclude_paths=["root['_id']", "root['_vault_md']"])
            dicted = differencer.to_dict()
            dicted["itemtype"] = "kubernetesconfigchange"
            jsoned = json_dumps(dicted, default_mapping=None)
            
            # Send the changes to immudb.io
            inserted = s.put("https://vault.immudb.io/ics/api/v1/ledger/default/collection/default/document", 
                             data=jsoned)
            assert inserted.status_code == 200

            # Print the fields that have changed
            changes = differencer.to_dict()
            for change_type, details in changes.items():
                if change_type == 'values_changed':
                    print("The following fields have changed values:")
                    for path, changes in details.items():
                        print(f"Field: {path}, old value: {changes['old_value']}, new value: {changes['new_value']}")
                elif change_type in ('iterable_item_added', 'iterable_item_removed'):
                    print(f"Items have been {change_type} in the following fields:")
                    for path in details:
                        print(f"Field: {path}")
                elif change_type == 'type_changes':
                    print("The following fields have changed type:")
                    for path, changes in details.items():
                        print(f"Field: {path}, old type: {changes['old_type']}, new type: {changes['new_type']}")

            print(f"Configuration change for pod {pod.metadata.name} has been sent to the vault")

