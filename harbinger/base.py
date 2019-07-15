import abc
import os
import oyaml as yaml

from cliff.command import Command
from configobj import ConfigObj
from oslo_config import cfg
from oslo_log import log as logging
from six import add_metaclass

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

OPTS = []


def register_opt_group(conf, opt_group, options):
    if opt_group:
        if opt_group.name not in conf:
            conf.register_group(opt_group)
    for opt in options:
        if opt.dest not in conf[opt_group.name]:
            conf.register_opt(opt, group=getattr(opt_group, 'name', None))


def harbingeropts(harbinger_config_file):
    if not os.path.exists(harbinger_config_file):
        raise IOError('%s file not present ' % harbinger_config_file)

    # this section dynamically loads oslo_config objects from the cfg file
    # this prevents devs from having to manually update the opts, all that is
    # required is to update the cfg
    config = ConfigObj(harbinger_config_file)
    group_variables = {}
    for section in config.sections:
        group_variables[section.upper() +
                        '_GROUP'] = cfg.OptGroup(name=section)
        group_opts = config[section]
        opt_list = []
        for item in group_opts:
            opt_list.append(cfg.StrOpt(item))
        OPTS.append((group_variables[section.upper() + '_GROUP'], opt_list))
        group_variables.clear()

    args = ['--config-file', harbinger_config_file]
    CONF(args=args)
    return CONF


harbingeropts(
    os.path.dirname(os.path.realpath(__file__)) + '/etc/harbinger.cfg')
for group, option in OPTS:
    register_opt_group(CONF, group, option)


@add_metaclass(abc.ABCMeta)
class Base(Command):
    def __init__(self, app, app_args, cmd_name=None):
        super(Base, self).__init__(app, app_args, cmd_name)
        self.framework_dict = {}
        self.environment = None

    def take_action(self, parsed_args):
        pass

    def load_yaml(self, yaml_file):
        with open(yaml_file, 'r') as yaml_f:
            return yaml.load(yaml_f, Loader=yaml.FullLoader)


class CommandBase(Base):
    def get_parser(self, prog_name):
        parser = super(CommandBase, self).get_parser(prog_name)
        parser.add_argument(
            'yaml',
            metavar='<yaml>',
            default='',
            help=('Location of the yaml config file '
                  'to create relevant cfgs'),
        )
        return parser
