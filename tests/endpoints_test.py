import requests
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama (autoreset ensures clean output)
init(autoreset=True)

def test_endpoints_with_session(hostname, port, endpoints_config):
    base_url = f'http://{hostname}:{port}'
    session = requests.Session()
    failed_results = []

    passed = 0
    failed = 0

    for endpoint, allowed_statuses in endpoints_config.items():
        url = f'{base_url}{endpoint}'
        try:
            response = session.get(url)
            status = response.status_code
            if status in allowed_statuses:
                passed += 1
            else:
                failed_results.append((
                    f"{Fore.RED}FAIL{Style.RESET_ALL}",
                    endpoint,
                    f"{Fore.RED}{status}{Style.RESET_ALL}",
                    f"{Fore.GREEN}{allowed_statuses}{Style.RESET_ALL}"
                ))
                failed += 1
        except Exception as e:
            print(f"{Fore.YELLOW}ERROR{Style.RESET_ALL}: {endpoint} raised exception {e}")
            failed_results.append((
                f"{Fore.YELLOW}ERROR{Style.RESET_ALL}",
                endpoint,
                f"{Fore.YELLOW}{str(e)}{Style.RESET_ALL}",
                f"{Fore.GREEN}{allowed_statuses}{Style.RESET_ALL}"
            ))
            failed += 1

    print("\n" + "=" * 60)
    print(f"{Style.BRIGHT}Test Summary:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Passed:{Style.RESET_ALL} {passed}")
    print(f"{Fore.RED}Failed:{Style.RESET_ALL} {failed}")
    print("=" * 60)

    if failed_results:
        print(f"{Style.BRIGHT}Failures & Errors:{Style.RESET_ALL}")
        print(tabulate(
            failed_results,
            headers=["Result", "Endpoint", "Status", "Expected"],
            tablefmt="grid"
        ))
    else:
        print(f"{Fore.GREEN}All endpoints returned expected status codes.{Style.RESET_ALL}")


# Define endpoint config: endpoint -> list of acceptable status codes
endpoints_config = {
    "/favicon.ico": [200],
    "/tyre-icons/soft.svg": [200],
    "/tyre-icons/super-soft.svg": [200],
    "/tyre-icons/medium.svg": [200],
    "/tyre-icons/hard.svg": [200],
    "/tyre-icons/intermediate.svg": [200],
    "/tyre-icons/wet.svg": [200],
    "/": [200],
    "/eng-view": [200],
    "/player-stream-overlay": [200],
    "/telemetry-info": [200],
    "/race-info": [200],
    "/driver-info?index=0": [200],
    "/stream-overlay-info": [200],
    "/static/css/style.css": [200],
    "/static/css/modals.css": [200],
    "/static/css/weather.css": [200],
    "/static/css/conditions.css": [200],
    "/static/css/speedLimit.css": [200],
    "/static/css/tyreStintHistoryModal.css": [200],
    "/static/js/preferences.js": [200],
    "/static/js/utils.js": [200],
    "/static/js/iconCache.js": [200],
    "/static/js/weatherUI.js": [200],
    "/static/js/graph.js": [200],
    "/static/js/driverDataModalPopulator.js": [200],
    "/static/js/raceStatsModalPopulator.js": [200],
    "/static/js/tyreStintHistoryModal.js": [200],
    "/static/js/modals.js": [200],
    "/static/js/raceTableRowPopulator.js": [200],
    "/static/js/timeTrialDataPopulator.js": [200],
    "/static/js/telemetryRenderer.js": [200],
    "/static/js/frontendUpdate.js": [200],
    "/static/js/app.js": [200],
    "/static/js/updater.js": [200],
}

# Example hostname and port
hostname = "localhost"
port = 4768

test_endpoints_with_session(hostname, port, endpoints_config)
