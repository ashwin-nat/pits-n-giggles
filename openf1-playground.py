import requests
import json

def make_openf1_request(endpoint, params=None):
    base_url = "https://api.openf1.org/v1/"
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def fetch_f1_sessions():
    params = {
        "date_start>": "2024-03-01",
        "date_end<": "2024-12-10"
    }
    return make_openf1_request("sessions", params)

def fetch_f1_session_winner(session_key=7782):
    params = {
        "session_key": session_key,
        # The OpenF1 API expects "position<" for less than or equal to,
        # and the requests library will correctly encode '<' as '%3C'.
        "position<": 1
    }
    return make_openf1_request("session_result", params)

if __name__ == "__main__":
    if rsp := fetch_f1_sessions():
        print("got sessions")
        # build the dict

        # Get list of circuits
        circuit_map = {item["circuit_short_name"]: item["circuit_key"] for item in rsp}
        print(circuit_map)
    else:
        print("failed to get sessions")

    print('*' * 50)
    if rsp := fetch_f1_session_winner():
        print("got session winner")
        print(json.dumps(rsp, indent=4))
    else:
        print("failed to get session winner")