import json
import os
from collections import Counter # Useful for counting severities

ALERTS_FILE = "alerts.json"

def load_alerts_data(selected_tenant=None, authorized_tenants=None):
    """
    Loads alert data from ALERTS_FILE.

    Args:
        selected_tenant (str, optional): The specific tenant selected by the user.
                                         If None, consider alerts from all authorized_tenants.
        authorized_tenants (list, optional): A list of tenant IDs the user is authorized to see.
                                             Used when selected_tenant is None or 'All Tenants'.

    Returns:
        tuple: (total_alerts_count, security_events_count, severity_counts)
               - total_alerts_count: Number of alerts for the specified tenant(s).
               - security_events_count: Number of 'Critical' or 'High' severity alerts.
               - severity_counts: Dictionary with counts for each severity level.
    """

    current_script_path = os.path.dirname(os.path.abspath(__file__))
    alerts_file_path = os.path.join(current_script_path, ALERTS_FILE)

    if not os.path.exists(alerts_file_path):
        try:
            with open(alerts_file_path, "w") as f:
                json.dump([], f)
        except IOError:
             return 0, 0, {}
        return 0, 0, {}

    try:
        with open(alerts_file_path, "r") as f:
            alerts_from_file = json.load(f) # Renamed to avoid conflict
    except json.JSONDecodeError:
        return 0, 0, {}
    except IOError:
        return 0, 0, {}

    if not isinstance(alerts_from_file, list):
        return 0, 0, {}

    relevant_alerts = []

    target_tenant_ids = set()
    if selected_tenant and selected_tenant != "All Tenants":
        target_tenant_ids.add(selected_tenant)
    elif authorized_tenants: # This covers "All Tenants" if authorized_tenants is populated
        target_tenant_ids.update(authorized_tenants)

    # If target_tenant_ids is empty at this point, it means neither a specific tenant
    # nor a list of authorized tenants was provided to filter by.
    # In this scenario, we might want to show all alerts (e.g. for an unrestricted admin view).
    # The current logic will result in relevant_alerts remaining empty if target_tenant_ids is empty,
    # unless we explicitly decide to load all alerts if target_tenant_ids is empty.

    if not target_tenant_ids: # No specific filters provided, load all alerts.
        for alert_in_file in alerts_from_file:
            if isinstance(alert_in_file, dict): # Basic validation of alert structure
                 relevant_alerts.append(alert_in_file)
    else:
        for alert_in_file in alerts_from_file:
            if not isinstance(alert_in_file, dict):
                continue
            alert_tenant_id = alert_in_file.get("tenant_id")
            if alert_tenant_id in target_tenant_ids:
                relevant_alerts.append(alert_in_file)

    # Calculate severity counts
    severity_counts = Counter()
    for alert in relevant_alerts:
        severity = alert.get("severity", "Unknown") # Default to "Unknown" if severity key is missing
        severity_counts[severity] += 1

    total_alerts_count = len(relevant_alerts)

    # Security events are Critical or High
    security_events_count = severity_counts.get("Critical", 0) + severity_counts.get("High", 0)

    return total_alerts_count, security_events_count, dict(severity_counts)
