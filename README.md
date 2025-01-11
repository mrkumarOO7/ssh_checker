# SSH Connectivity Checker and Ansible Inventory Generator

This project provides a Python script to automate the following tasks:

1. Parse an SSH configuration file (`~/.ssh/config`) to extract agency-host mappings.
2. Check SSH connectivity for the hosts defined in the SSH config.
3. Generate an Ansible inventory file with one working host per agency.
4. Export a CSV file detailing the SSH connectivity results.
5. Manage log directories by cleaning up old directories (default: older than 2 days).

## Features

- **Save Location Management**: Ensures logs and results are stored in an organized directory structure.
- **SSH Config Parsing**: Reads and processes the `~/.ssh/config` file.
- **Multithreaded SSH Connectivity Checks**: Optimized connectivity checks using multithreading.
- **Ansible Inventory Generation**: Automatically creates an inventory file in the expected Ansible format.
- **Detailed Reporting**: Exports connectivity results to a CSV file for auditing.
- **Automatic Cleanup**: Removes log directories older than a configurable threshold.

## Requirements

- Python 3.6+
- The following Python libraries:
  - `paramiko`
  - `csv`
  - `datetime`
  - `threading`
  - `os`
  - `shutil`

Install dependencies using:
```bash
pip install paramiko
```

## Setup and Usage

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Ensure your SSH configuration is available at `~/.ssh/config` or modify the script to specify a custom path.

3. Run the script:
    ```bash
    python script_name.py
    ```

4. Outputs:
    - A log directory is created under `ssh_logs/` in the current working directory.
    - **Ansible Inventory File**: Saved as `ansible_inventory.ini`.
    - **CSV Report**: Saved as `ssh_check_results.csv`.

## Configuration

### Change Save Location
You can update the save directory by modifying the `get_save_location()` function in the script.

### Cleanup Threshold
The default cleanup threshold is 2 days. Modify the `cleanup_old_directories` function call in `main()` to adjust this value:
```python
cleanup_old_directories(base_dir, days=2)
```

### Custom SSH Config Path
Change the path to the SSH configuration file:
```python
ssh_config_path = "/custom/path/to/ssh_config"
```

## Outputs

- **Ansible Inventory File**:
    - Contains one working host per agency in the required format.
    - Includes Ansible variables for authentication.

    Example:
    ```ini
    [all:vars]
    ansible_ssh_common_args='-o StrictHostKeyChecking=no'
    ansible_python_interpreter=/usr/bin/python3
    ansible_ssh_user=ccadmin
    ansible_ssh_password='BFLserv#2024'
    ansible_become_pass='BFLserv#2024'

    [agency1]
    host1.example.com:22

    [agency2]
    host2.example.com:22
    ```

- **CSV Report**:
    - Columns: Agency, Host, Port, Status, Reason
    - Includes detailed results for all hosts checked.

    Example:
    ```csv
    Agency,Host,Port,Status,Reason
    agency1,host1.example.com,22,Reachable,
    agency2,host2.example.com,22,Unreachable,Timeout
    ```

## Multithreading
The script uses Python's `threading` module to parallelize SSH checks for faster execution.

## Error Handling
- The script gracefully handles missing SSH config files and unreachable hosts.
- Errors are logged to the console for debugging purposes.

## Future Enhancements

- Add unit tests for key functions.
- Support user-defined SSH config paths and custom Ansible templates.
- Implement logging to file instead of console.
- Include retry logic for failed SSH connections.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

Feel free to raise issues or contribute to this project through pull requests.
