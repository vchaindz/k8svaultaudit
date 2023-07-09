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

### Running the Script
You can run the script from the command line as follows:

```
python k8s_config_monitor.py --kubeconfig /path/to/your/kubeconfig --namespace yournamespace
```

### Environment Variables

- `KUBECONFIG`: Path to your kubeconfig file. If not set, the script will look for the kubeconfig file at `/path/to/your/kubeconfig`.
- `NAMESPACE`: Specific namespace to monitor. If not set, the script will monitor all namespaces.

## Note

This script is primarily for educational and testing purposes. It does not handle potential exceptions that may occur during file operations, such as permissions issues or insufficient disk space. Please enhance error handling if you wish to use it in a production environment.

