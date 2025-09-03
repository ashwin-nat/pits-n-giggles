import requests
import json

def fetch_f1_sessions():
    url = "https://api.openf1.org/v1/sessions?date_start%3E=2024-03-01&date_end%3C=2024-12-10"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
        # for session in sessions:
        #     print(session)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching F1 sessions: {e}")

if __name__ == "__main__":
    rsp = fetch_f1_sessions()
    print("got data")
    # build the dict

    # Get list of circuits
    circuit_map = {item["circuit_short_name"]: item["circuit_key"] for item in rsp}
    print(circuit_map)

