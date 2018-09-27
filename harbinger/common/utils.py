import os

from oslo_config import cfg
from oslo_log import log as logging

from harbinger.factory.base import BaseFactory

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Utils(object):
    @staticmethod
    def load_class(dottedpath):
        """Load a class from a module in dotted-path notation.

        E.g.: load_class("package.module.class").

        """
        if not dottedpath:
            raise ValueError("dottedpath must not be None")

        splitted_path = dottedpath.split('.')
        modulename = '.'.join(splitted_path[:-1])
        classname = splitted_path[-1]
        try:
            try:
                module = __import__(modulename, globals(), locals(),
                                    [classname])
            except ValueError:  # Py < 2.5
                if not modulename:
                    module = __import__(__name__.split('.')[0],
                                        globals(), locals(), [classname])
        except ImportError:
            # properly log the exception information and return None
            # to tell caller we did not succeed
            LOG.exception('tg.utils: Could not import %s'
                          ' because an exception occurred', dottedpath)
            return None
        try:
            return getattr(module, classname)
        except AttributeError:
            LOG.exception('tg.utils: Could not import %s'
                          ' because the class was not found', dottedpath)
            return None

    @staticmethod
    def get_supported_frameworks():
        directory = os.path.dirname(os.path.dirname(__file__)) + "/executors"
        supported_frameworks = []

        for filename in os.listdir(directory):
            if "pyc" not in filename:
                name = os.path.splitext(filename)[0]
                # cross check the file name, if framework is valid it will
                # have an entry in cfg file
                try:
                    CONF.get(name)
                    supported_frameworks.append(name)
                except cfg.NoSuchOptError:
                    pass

        return sorted(supported_frameworks)

    @staticmethod
    def hierarchy_lookup(executor, prop):
        """lookup values using hierarchy

         this method looks up values by object hierarchy.
         The order, listed by priority is:
         (Execute -> Framework)
           extras
           options_override
         (Options)
         (Harbinger.cfg)

         This priority list will be traversed in reverse, so the highest
         priority object is the one returned
         """
        result = [None]

        # ensure the "optional" fields in input yaml have a default value
        # to prevent any errors in lookup
        hierarchy = (CONF[executor.framework.name],
                     executor.options,
                     executor.framework.options_override
                     if 'options_override' in vars(executor.framework) else {},
                     executor.framework.extras
                     if 'extras' in vars(executor.framework) else {},
                     executor.framework.required)

        for obj in hierarchy:
            item = None
            if isinstance(obj, dict):
                item = obj.get(prop)

            if isinstance(obj, BaseFactory):
                attr = getattr(obj, prop, None)
                if attr is not None:
                    item = attr

            if isinstance(obj, cfg.ConfigOpts.GroupAttr):
                attr = getattr(obj, prop, None)
                if attr is not None:
                    item = attr

            if item is not None:
                result.append(item)

        return result[-1]

    @classmethod
    def source_openrc(cls, executor):
        """set additional openstack related environment variables

         This sets the additional openstack related environment variables
         that are needed at a minimum to connect to the api. Other neccessary
         variables are specified in the input yaml and enforced via the schema
         so they should already be set.
         """
        os.environ['OS_USERNAME'] = cls.hierarchy_lookup(
            executor, 'username')
        os.environ['OS_PASSWORD'] = cls.hierarchy_lookup(
            executor, 'password')
        os.environ['OS_PROJECT_NAME'] = cls.hierarchy_lookup(
            executor, 'project')
        os.environ['EXTERNAL_NETWORK'] = cls.hierarchy_lookup(
            executor, 'external_network')
