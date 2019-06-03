"""
Images class:
    - handle image management for the supported data plane testing framworks
"""
import os

from glanceclient import Client
from keystoneauth1 import loading
from keystoneauth1 import session

from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ImageManager():
    def __init__(self, label, **kwargs):
        loader = loading.get_plugin_loader('password')

        auth = loader.load_from_options(**kwargs)
        session2 = session.Session(auth=auth)

        LOG.info(
            'Creating Glance client for %s using keystone: %s',
            label, kwargs.pop('auth_url'))

        self.glance = Client('2', session=session2)

    def check_image(self, image_name):
        image_exists = False
        for image in self.glance.images.list():
            if image['name'] == image_name:
                image_exists = True
                break

        LOG.info('Image <%s> exists in Glance: %s', image_name, image_exists)
        return image_exists

    def upload_image(self, image_name, disk_format, container_format,
                     image_path=None):

        if image_path is None:
            image_path = os.path.join(CONF.DEFAULT.files_dir, "images")

        image_file = None
        for file in os.listdir(image_path):
            if image_name in file:
                image_file = file
                break

        if image_file is not None:
            full_path = os.path.join(image_path, image_file)
            img = self.glance.images.create(name=image_name,
                                            disk_format=disk_format,
                                            container_format=container_format)

            LOG.info('Uploading image <%s> into Glance....', image_name)
            try:
                self.glance.images.upload(img.id, open(full_path, 'rb'))
            except Exception as ex:
                msg = 'Error connecting to Glance, ' \
                      'check proxy and no_proxy settings\n' + str(ex)
                LOG.error(msg)
                raise

            LOG.info('Image <%s> uploaded into Glance', image_name)
        else:
            raise OSError('Image upload error: %s could not be found in %s' % (
                image_name, image_path))
