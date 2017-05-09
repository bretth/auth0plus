from .management.rest import RestClient


def get_token(domain, client_id, client_secret):
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "https://%s/api/v2/" % domain}
    url = 'https://%s/oauth/token' % domain
    client = RestClient()
    return client.post(url, payload)
