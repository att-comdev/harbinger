"""
Flavor class:
    - handle flavor management for the supported data plane testing framworks
"""
from keystoneauth1 import loading
from keystoneauth1 import session
from novaclient import client

from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class FlavorManager():
    def __init__(self, label, **kwargs):
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**kwargs)
        session2 = session.Session(auth=auth)

        LOG.info('Creating Nova client for %s using keystone: %s', label,
                 kwargs.pop('auth_url'))

        self.nova = client.Client(2, session=session2)

    def check_flavor(self, flavor_name):
        flavor_exists = False
        for flavor in self.nova.flavors.list():
            if flavor.name == flavor_name:
                flavor_exists = True
                break

        LOG.info('Flavor <%s> exists: %s', flavor_name, flavor_exists)
        return flavor_exists

    def create_flavor(self,
                      name,
                      ram,
                      vcpus,
                      disk,
                      flavorid='auto',
                      ephemeral=0,
                      swap=0,
                      rxtx_factor=1.0,
                      is_public=True,
                      description=None):
        LOG.info('Creating flavor %s', name)

        self.nova.flavors.create(name,
                                 ram,
                                 vcpus,
                                 disk,
                                 flavorid=flavorid,
                                 ephemeral=ephemeral,
                                 swap=swap,
                                 rxtx_factor=rxtx_factor,
                                 is_public=is_public,
                                 description=description)
