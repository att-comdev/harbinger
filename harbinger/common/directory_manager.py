"""
Directory Manager class:
    - A class that manages and sets up directorys that harbinger
    will use throughout its execution
"""
import datetime
import os
import time
import uuid

from oslo_config import cfg
from oslo_log import log as logging
from prettytable import PrettyTable

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class DirectoryManager():
    def setup(self):
        self.inputs_dir = os.path.join(CONF.DEFAULT.files_dir, "inputs")
        self.outputs_dir = os.path.join(CONF.DEFAULT.files_dir, "outputs")
        self.create_inputs_dir()
        self.create_outputs_dir()

    def create_inputs_dir(self):
        if not os.path.isdir(self.inputs_dir):
            os.makedirs(self.inputs_dir)

    def create_outputs_dir(self):
        if not os.path.isdir(self.outputs_dir):
            os.makedirs(self.outputs_dir)

    def archive_outputs(self):
        archive_id = str(uuid.uuid4())[:5]
        time_stamp = time.time()
        std_time = datetime.datetime.fromtimestamp(time_stamp).strftime(
            '%Y-%m-%d %H:%M:%S')

        archive_list = []
        for (dirpath, dirnames, filenames) in os.walk(self.outputs_dir):
            for file_name in filenames:
                if 'hrb' not in file_name:
                    root_name = file_name.split('.')[0]
                    try:
                        ext = file_name.split('.')[1]
                    except IndexError:
                        ext = 'hrb'

                    name_format = '{}-{}-hrb.{}'
                    new_name = name_format.format(root_name, archive_id, ext)
                    os.rename(os.path.join(self.outputs_dir, file_name),
                              os.path.join(self.outputs_dir, new_name))

                    archive_list.append(new_name)
            break

        if archive_list:
            archive_name = 'archive-hrb.log'
            archive_path = os.path.join(self.outputs_dir, archive_name)

            LOG.info('Archiving previous outputs, see %s for details',
                     archive_path)

            table = PrettyTable()
            table.field_names = [std_time]

            for item in archive_list:
                table.add_row([item])

            with open(archive_path, "a") as archive_file:
                archive_file.write(str(table) + '\n\n')
