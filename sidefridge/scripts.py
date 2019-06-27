import os

from sidefridge.utils import print_logger

AFTER_BACKUPS = 'after_backups'
BACKUPS = 'backups'
BEFORE_BACKUPS = 'before_backups'
INSTALL_DEPENDENCIES = 'install_dependencies'
ON_ERROR = 'on_error'

SUPPORTED_DIRECTORIES = {AFTER_BACKUPS, BACKUPS, BEFORE_BACKUPS, INSTALL_DEPENDENCIES, ON_ERROR}


class ScriptsDetector(object):
    def __init__(self, scripts_path):
        self.path = scripts_path
        self.detected_scripts = []

        sub_dirs_in_path = [
            x for x in os.listdir(self.path)
            if os.path.isdir(os.path.join(self.path, x)) and x in SUPPORTED_DIRECTORIES
        ]

        for sub_dir in sub_dirs_in_path:
            files = sorted([
                os.path.join(self.path, sub_dir, x) for x in os.listdir(os.path.join(self.path, sub_dir))
                if os.path.isfile(os.path.join(self.path, sub_dir, x))
            ])

            self.detected_scripts.append((sub_dir, files))
            setattr(self, "_" + sub_dir, files)

    def _get_attribute(self, attribute_name):
        return getattr(self, "_" + attribute_name, [])

    @property
    def after_backups(self):
        return self._get_attribute(AFTER_BACKUPS)

    @property
    def backups(self):
        return self._get_attribute(BACKUPS)

    @property
    def before_backups(self):
        return self._get_attribute(BEFORE_BACKUPS)

    @property
    def install_dependencies(self):
        return self._get_attribute(INSTALL_DEPENDENCIES)

    @property
    def on_error(self):
        return self._get_attribute(ON_ERROR)

    def list_detected_scripts(self):
        message = "\n** Detected scripts **\n"
        for category, scripts in self.detected_scripts:
            message += "-- %s --\n" % category
            message += "%s\n" % scripts
        print_logger(message)
