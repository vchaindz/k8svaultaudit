# Kubernetes Configuration Change Monitor

This Python script monitors changes in Kubernetes pod configurations and writes the changed configurations to local JSON files.

The script continuously checks the current configurations of pods, comparing them with previously seen configurations. If a configuration change is detected, the old and new configurations are written to separate JSON files. These files are named after the pod and tagged as 'old' and 'new' configurations.

## Features
- The script allows users to specify the path to the kubeconfig file via a command-line flag or an environment variable.
- Users can limit the script to watch a specific namespace through command-line flag or environment variable.
- Detects and stores changes in configurations, allowing you to keep track of what changes have been made.

## Usage

### Prerequisites
Make sure you have installed the necessary Python packages listed in the `requirements.txt` file:

```
pip install -r requirements.txt
```

You will need the Python Kubernetes client and DeepDiff modules installed.

### Running the Script
You can run the script from the command line as follows:

```
python k8s_config_tracker.py --kubeconfig=/path/to/kubeconfig --namespace=monitoring --apikey=your_vault_api_key
```

The arguments are as follows:

--kubeconfig: Path to the kubeconfig file. If not provided, the KUBECONFIG environment variable or a default path is used.
--namespace: The specific namespace to monitor. If not provided, all namespaces are monitored.
--apikey: The API key for the vault.immudb.io service.
All these arguments are optional. If not provided, the script will try to use environment variables or a default configuration.

### Environment Variables

- `KUBECONFIG`: Path to your kubeconfig file. If not set, the script will look for the kubeconfig file at `/path/to/your/kubeconfig`.
- `NAMESPACE`: Specific namespace to monitor. If not set, the script will monitor all namespaces.
- `VAULT_IMMUDB_API_KEY`: Specify immudb Vault API Key. Register at [immudb Vault](https://vault.immudb.io)  

Operation
The script first loads the Kubernetes configuration from the specified kubeconfig file, or the KUBECONFIG environment variable or a default path.

It then enters a loop where it retrieves all pods either from the specified namespace, or all namespaces if none was specified. It then checks each pod's configuration against the stored hash of its configuration.

If a pod is new, or its configuration has changed, the new configuration is sent to the vault.immudb.io service, and the configuration is stored locally for future comparisons.

When a configuration change is detected, a difference report is generated detailing which fields changed, and how. This report is sent to the vault and printed to the console.

You can set the KUBECONFIG, NAMESPACE, and VAULT_IMMUDB_API_KEY environment variables instead of providing command line arguments.

## Notes

This script requires Python 3.6+ to run. It uses the Kubernetes and requests Python modules, which can be installed via pip.

