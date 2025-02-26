import requests
import pandas as pd
import sys, os
import numpy as np


if os.path.exists('valid_links.txt'):
    valid_links = np.loadtxt('valid_links.txt', dtype=str)  # Use dtype=str to load as strings
    print(f"Loaded {len(valid_links)} valid links.")

else:
    # List of candidate URLs'
    possible_links = []
    valid_links = []

    for i in range(100,1000):
        possible_links.append(f'https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En&Id={i:03d}')

    # This is the URL that the site redirects to when the mission doesn't exist.
    base_url = "https://www.oas.org/EOMDatabase/moeInfo.aspx?Lang=En"

    for link in possible_links:
        try:
            # Use GET to ensure redirections are fully followed
            response = requests.get(link, allow_redirects=True, timeout=7)
            if response.status_code == 200:
                # Check if the final URL still contains the "Id=" parameter.
                # If not, it means the page was not found and it was redirected to the base URL.
                if "Id=" in response.url:
                    valid_links.append(link)
                    print(f"Valid link: {link}")
                else:
                    print(f"Invalid link (redirected to base): {link}")
            else:
                print(f"Non-200 response for {link}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error checking {link}: {e}")

    np.savetxt('valid_links.txt', np.array(valid_links), fmt='%s')
    print(f"Saved {len(valid_links)} valid links to 'valid_links.txt'.")
