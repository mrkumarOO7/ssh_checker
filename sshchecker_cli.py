import os
import paramiko
import threading
import csv
import shutil
from datetime import datetime, timedelta
from collections import defaultdict

# Function to get the save location for files
def get_save_location():
    # Default location (same directory as the program)
    # To use a custom directory, uncomment the line below and provide the desired path
    # Example: save_path = r"C:\path\to\custom\location"
    save_path = os.getcwd()  # Default is the current working directory
    return save_path

# Parse the SSH config file
def parse_ssh_config(file_path):
    agencies = {}
    if not os.path.exists(file_path):
        print(f"SSH config file not found at {file_path}.")
        return agencies

    try:
        with open(file_path, "r") as file:
            current_host, current_config = None, {}
            for line in file:
                line = line.strip()
                if line.startswith("Host "):
                    if current_host and current_config:
                        agencies.setdefault(agency, []).append(current_config)
                    current_host = line.split()[1]
                    agency = current_host.split("_")[0] if "_" in current_host else current_host
                    current_config = {"host": current_host, "hostname": current_host, "port": 22}
                elif line.startswith("HostName "):
                    current_config["hostname"] = line.split()[1]
                elif line.startswith("Port "):
                    current_config["port"] = int(line.split()[1])
            if current_host and current_config:
                agencies.setdefault(agency, []).append(current_config)
    except Exception as e:
        print(f"Error parsing SSH config: {e}")
    return agencies

# Check SSH connectivity
def check_ssh_connectivity(hostname, port):
    try:
        transport = paramiko.Transport((hostname, port))
        transport.start_client()
        transport.close()
        return True, None
    except Exception as e:
        return False, str(e)

# Write results to Ansible inventory file
def write_ansible_inventory(file_path, inventory):
    try:
        with open(file_path, "w") as file:
            file.write("[all:vars]\n")
            file.write("ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n")
            file.write("ansible_python_interpreter=/usr/bin/python3\n")
            file.write("ansible_ssh_user=ccadmin\n")
            file.write("ansible_ssh_password='BFLserv#2024'\n")
            file.write("ansible_become_pass='BFLserv#2024'\n\n")

            # Sort agencies and hosts
            for agency in sorted(inventory.keys()):
                file.write(f"[{agency}]\n")
                for host in sorted(inventory[agency]):
                    file.write(f"{host}\n")
                file.write("\n")
        print(f"Ansible inventory saved to {file_path}")
    except Exception as e:
        print(f"Error writing inventory: {e}")

# Export results to CSV
def export_results_to_csv(csv_path, results):
    try:
        # Sort results by Agency and Host
        sorted_results = sorted(results, key=lambda x: (x[0], x[1]))

        with open(csv_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Agency", "Host", "Port", "Status", "Reason"])
            for result in sorted_results:
                writer.writerow(result)
        print(f"SSH check results exported to {csv_path}")
    except Exception as e:
        print(f"Error exporting results to CSV: {e}")

# Create a new directory for the current run
def create_run_directory(base_dir):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(base_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir

# Cleanup old directories
def cleanup_old_directories(base_dir, days=2):
    threshold_time = datetime.now() - timedelta(days=days)
    if not os.path.exists(base_dir):
        return

    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if os.path.isdir(entry_path):
            try:
                folder_time = datetime.strptime(entry, "%Y-%m-%d_%H-%M-%S")
                if folder_time < threshold_time:
                    shutil.rmtree(entry_path)
                    print(f"Deleted old directory: {entry_path}")
            except ValueError:
                continue  # Ignore directories with non-standard names

# Main function
def main():
    # Use the `get_save_location` function to determine the save location
    base_dir = os.path.join(get_save_location(), "ssh_logs")  # If want to change the directory name change this 
    cleanup_old_directories(base_dir)
    run_dir = create_run_directory(base_dir)

    ssh_config_path = os.path.expanduser("~/.ssh/config")
    ansible_inventory_path = os.path.join(run_dir, "ansible_inventory.ini")
    csv_path = os.path.join(run_dir, "ssh_check_results.csv")

    agencies = parse_ssh_config(ssh_config_path)
    if not agencies:
        print("No valid hosts found in SSH config.")
        return

    reachable_hosts = defaultdict(list)
    all_results = []
    threads = []
    lock = threading.Lock()

    def process_host(entry, agency):
        host, hostname, port = entry["host"], entry["hostname"], entry["port"]
        is_reachable, reason = check_ssh_connectivity(hostname, port)
        with lock:
            if is_reachable:
                reachable_hosts[agency].append(f"{hostname}:{port}")
                all_results.append((agency, hostname, port, "Reachable", ""))
            else:
                all_results.append((agency, hostname, port, "Unreachable", reason))

    for agency, hosts in agencies.items():
        for entry in hosts:
            thread = threading.Thread(target=process_host, args=(entry, agency))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    # Filter inventory to include only one working host per agency
    filtered_inventory = {
        agency: sorted(hosts[:1]) for agency, hosts in reachable_hosts.items() if hosts
    }

    # Save the inventory
    write_ansible_inventory(ansible_inventory_path, filtered_inventory)

    # Export results to CSV
    export_results_to_csv(csv_path, all_results)

if __name__ == "__main__":
    main()
