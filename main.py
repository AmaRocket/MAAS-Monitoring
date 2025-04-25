import os
import time
import uuid

import requests
from dotenv import load_dotenv
from flask import Flask, Response

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("MAAS_API_KEY")
if not API_KEY:
    print("MAAS_API_KEY environment variable is not set")
API_URL = os.getenv("MAAS_API_URL")
if not API_URL:
    print("MAAS_API_URL environment variable is not set")


def build_oauth_header(api_key):
    consumer_key, token, secret = api_key.split(":")
    oauth_nonce = str(uuid.uuid4())
    oauth_timestamp = str(int(time.time()))
    return (
        f"OAuth "
        f'oauth_version="1.0", '
        f'oauth_signature_method="PLAINTEXT", '
        f'oauth_consumer_key="{consumer_key}", '
        f'oauth_token="{token}", '
        f'oauth_signature="&{secret}", '
        f'oauth_nonce="{oauth_nonce}", '
        f'oauth_timestamp="{oauth_timestamp}"'
    )


def fetch_maas_machines():
    headers = {"Authorization": build_oauth_header(API_KEY)}
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "objects" in data:
            return data["objects"]  # paginated
        elif isinstance(data, list):
            return data  # plain list
        else:
            return []
    except Exception as e:
        print(f"Error fetching MAAS data: {e}")
        return []


@app.route("/metrics")
def metrics():
    machines = fetch_maas_machines()
    output = []

    for machine in machines:
        hostname = machine.get("hostname")
        power_status = machine.get("status_name")
        power = machine.get("power_state")
        status_message = machine.get("status_message")
        power_type = machine.get("power_type")
        zone_name = machine.get("zone", {}).get("name", "unknown")
        storage_test_status_name = machine.get("storage_test_status_name")

        status_message = str(status_message).strip()
        power_type_lower = str(power_type or "").lower()

        ignore_errors_if_power_ok = ["webhook", "ipmi"]

        if power in "on" and power_type_lower in ignore_errors_if_power_ok:
            status_message = ""

        # Clean up for Prometheus labels
        def escape(s):
            return s.replace('"', '\\"')

        output.append(
            f'maas_machine_status{{hostname="{escape(hostname)}",power_status="{escape(power_status)}", storage_test_status_name="{escape(storage_test_status_name)}", zone="{escape(zone_name)}"}} 1'
        )
        output.append(
            f'maas_machine_power_state{{hostname="{hostname}",power="{power}", status_message="{status_message}", power_type="{power_type}"}} 1'
        )

    return Response("\n".join(output), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9200)
