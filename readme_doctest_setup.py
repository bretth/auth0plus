#! /usr/bin/env python
"""
Setup doctests in README.txt

"""
import os
import requests
from dotenv import load_dotenv  # python-dotenv
from six.moves.urllib.parse import quote


def main():
    load_dotenv('.env')
    domain = os.getenv('DOMAIN')
    # client_id = os.getenv('CLIENT_ID')
    connection = os.getenv('CONNECTION')
    jwt = os.getenv('JWT')

    headers = {
        'Authorization': 'Bearer %s' % jwt,
    }
    params = {
        'connection': connection,
        'search_engine': 'v1'
    }
    # get all users on the test domain and connection
    url = 'https://%s/api/v2/users' % domain
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    all_users = resp.json()

    # delete them
    for user in all_users:
        user_id = quote(user['user_id'])
        print('deleting', user['email'])
        resp = requests.delete('/'.join([url, user_id]), headers=headers)
        print(resp)

if __name__ == '__main__':
    main()
