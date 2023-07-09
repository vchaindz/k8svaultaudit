import os
import json
import hashlib
import argparse
from kubernetes import client, config, watch
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Monitor Kubernetes configurations.')
parser.add_argument('--kubeconfig', type=str, help='Path to the kubeconfig file.')
parser.add_argument('--namespace', type=str, help='Specific namespace to monitor.')
args = parser.parse_args()

# Load Kubernetes configuration file from command line argument or environment variable
kube_config_path = args.kubeconfig or os.getenv('KUBECONFIG', '/path/to/your/kubeconfig')
config.load_kube_config(kube_config_path)

# Set the namespace to watch
namespace_to_watch = args.namespace or os.getenv('NAMESPACE', None)

v1 = client.CoreV1Api()

# Store hashes and configurations of pods
pod_data_store = {}

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

while True:
    # Get all pods
    if namespace_to_watch:
        pods = v1.list_namespaced_pod(namespace=namespace_to_watch, watch=False)
    else:
        pods = v1.list_pod_for_all_namespaces(watch=False)
    
    for pod in pods.items:
        # Convert pod data to JSON, handling datetime objects
        pod_data = json.dumps(pod.to_dict(), sort_keys=True, default=datetime_handler)
        # Hash the JSON data
        pod_hash = hashlib.sha256(pod_data.encode('utf-8')).hexdigest()
        
        if pod.metadata.name not in pod_data_store:
            # If the pod is new, add it to the data store
            pod_data_store[pod.metadata.name] = {'hash': pod_hash, 'config': pod_data}
        elif pod_data_store[pod.metadata.name]['hash'] != pod_hash:
            # If the pod configuration has changed, update the data store and print a message
            old_config_file_path = f'{pod.metadata.name}_old_config.json'
            old_config_file = open(old_config_file_path, 'w')
            old_config_file.write(pod_data_store[pod.metadata.name]['config'])
            old_config_file.close()
            print(f"Previous configuration for pod {pod.metadata.name} has been written to {old_config_file_path}")

            pod_data_store[pod.metadata.name] = {'hash': pod_hash, 'config': pod_data}
            
            new_config_file_path = f'{pod.metadata.name}_new_config.json'
            new_config_file = open(new_config_file_path, 'w')
            new_config_file.write(pod_data)
            new_config_file.close()
            print(f"New configuration for pod {pod.metadata.name} has been written to {new_config_file_path}")

