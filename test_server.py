"""
test_server.py

This file contains functions for testing the server.
"""
import argparse
import requests
import json


def parse_args():
    parser = argparse.ArgumentParser(description="Tests the server with test birth information.")

    parser.add_argument("url", help="The URL of the server.")
    parser.add_argument("date", help="The date of birth. Must be in the format YYYY/MM/DD.")
    parser.add_argument("time", help="The time of birth. Must be in one of the following forms:"
                        " HH:MM, HH:MM@HH:MM, HH:MM:SS, HH:MM:SS@HH:MM:SS, where '@' can be '-' or '+'.")
    parser.add_argument("place", help="The location of birth. Must be in the form CITY, STATE, COUNTRY,"
                        " where STATE and COUNTRY are optional but recommended for disambiguation purposes.")

    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()

    # Create test data
    # Example test data
    # test_data = {"birthDate": "1995/02/07", "birthTime": "08:00-06:00", "birthPlace": "Round Rock, TX"}
    test_data = {"birthDate": args.date,
                 "birthTime": args.time,
                 "birthPlace": args.place}

    # Test server response
    response = requests.post(args.url, json=test_data)

    json_res = json.loads(response.text)
    for part in json_res:
        content = json_res[part]
        if type(content) is dict:
            print(part)
            for subpart in content:
                print(subpart + ": " + str(content[subpart]))
        else:
            print(part + ": " + str(json_res[part]))
        print("")
