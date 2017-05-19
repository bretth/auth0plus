from .management.rest import RestClient


def get_token(domain, client_id, client_secret, grant_type="client_credentials"):
    """
    Get an auth0 client_credentials token
    https://auth0.com/docs/api/management/v2/tokens
    """

    payload = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "https://%s/api/v2/" % domain}
    url = 'https://%s/oauth/token' % domain
    client = RestClient()
    return client.post(url, payload)
