from ..settings import TIMEOUT
# from .blacklists import Blacklist
# from .clients import Client
# from .connections import Connection
# from .device_credentials import DeviceCredential
# from .emails import Email
# from .jobs import Job
from .rest import RestClient
# from .rules import Rule
# from .stats import Stat
# from .tenants import Tenant
# from .tickets import Ticket
from .users import User


class Auth0(object):
    """Provides easy access to all endpoint classes

    Args:
        domain (str): Your Auth0 domain, e.g: 'username.auth0.com'

        token (str): An API token created with your account's global
            keys. You can create one by using the token generator in the
            API Explorer: https://auth0.com/docs/api/v2

        client_id (str): Optional. The Auth0 client id - used for updating some user attributes

        default_connection (str): Optional default user connection

        timeout (int): Optional timeout in seconds.

        session: Optional requests.Session instance
    """
    
    def __init__(self, domain, token, client_id='', default_connection='',
                 timeout=TIMEOUT, session=None):
        # set some defaults for the endpoint classes
        self._client = RestClient(token, session=session)
        self._base_url = 'https://%s/api/v2' % domain
        self._default_connection = default_connection

        defaults = {
            '_base_url': self._base_url,
            '_client': self._client,
            '_timeout': timeout,
        }
        
        endpoints = [
            # Blacklist,
            # Client,
            # Connection,
            # DeviceCredential,
            # Email,
            # Job,
            # Rule,
            # Stat,
            # Tenant,
            # Ticket,
            User]

        setattr(User, '_default_connection', self._default_connection)
        setattr(User, '_default_client_id', client_id)
        # attach endpoints
        for endpoint in endpoints:
            _set_endpoint_attributes(self, endpoint, defaults)


def _set_endpoint_attributes(parent, endpoint, defaults):
    """
    Walk the endpoint and their children endpoints attaching children to their parent and
    setting default connection attributes
    """
    url = '/'.join([defaults.get('_base_url', ''), endpoint._path])
    setattr(endpoint, '_endpoint', url)
    for key, value in defaults.items():
        setattr(endpoint, key, value)
    path = endpoint._path.split('/')[-1]
    setattr(parent, path.replace('-', '_'), endpoint)
    if getattr(endpoint, '_endpoints', False):
        for child in endpoint._endpoints:
            _set_endpoint_attributes(endpoint, child, defaults)

    




