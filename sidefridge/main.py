import argparse
import os
import subprocess
import sys

from croniter import croniter

from sidefridge.scripts import ScriptsDetector
from sidefridge.storage import clear_storage
from sidefridge.utils import print_logger

HERE = os.path.dirname(os.path.realpath(__file__))

CRON_BACKUP_SCHEDULE = "CRON_BACKUP_SCHEDULE"

CRON_TEMPLATE = """%s fridge -r
# remember to end this file with an empty new line
"""


class SubprocessErrorDuringExecutionException(Exception):
    pass


class ScriptErrorOccurred(Exception):
    pass


def run_single_script(script, skip_error=False, **kwargs):
    print_logger("Starting '%s'" % script)
    cmd = [script] + list(kwargs.values())
    print_logger(cmd)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.write(c.decode('utf-8'))

    process.communicate()
    exit_code = process.returncode

    if exit_code != 0:
        error_message = "Script '%s' finished with exit code '%s'" % (script, exit_code)
        if skip_error:
            print_logger(error_message)
        else:
            raise SubprocessErrorDuringExecutionException(error_message)


def run_scripts(scripts_detector, path, hook_name):
    """
    Will run scripts in a given directory, if an error occurs it will launch on_error scripts.
    If an error occurs during an on_error script, the entire chain of scripts will stop.
    """
    print_logger("Hook: '%s'" % hook_name)
    try:
        for script in path:
            run_single_script(script)
    except SubprocessErrorDuringExecutionException as e:
        print_logger(e)
        # run on_error callbacks and do not rejigger on_error
        for error_script in scripts_detector.on_error:
            run_single_script(error_script, skip_error=True, error=str(e))
        raise ScriptErrorOccurred("Script execution finished due to errors. Look at logs for details")


def start_initialize(scripts_detector, cron_path):
    cron_schedule_content = CRON_TEMPLATE % os.environ[CRON_BACKUP_SCHEDULE]

    with open(cron_path, 'w') as cron_file:
        cron_file.write(cron_schedule_content)

    try:
        run_scripts(scripts_detector, scripts_detector.install_dependencies, 'install_dependencies')
    except ScriptErrorOccurred as e:
        # int the dependency install phase it is important to fail and do not boot the container
        print_logger(e)
        raise e


def start_run(scripts_detector):
    # always clean storage before and after usage, we do not want to leave unattended data between calls
    clear_storage()
    try:
        run_scripts(scripts_detector, scripts_detector.before_backups, 'before_backups')
        run_scripts(scripts_detector, scripts_detector.backups, 'backups')
        run_scripts(scripts_detector, scripts_detector.after_backups, 'after_backups')
    except ScriptErrorOccurred as e:
        print_logger(e)
    finally:
        clear_storage()


def main():
    parser = argparse.ArgumentParser(
        description='Tool for running and initializing backup container'
    )
    parser.add_argument(
        '-i', '--initialize', action='store_true',
        help='configure cron and install dependencies'
    )
    parser.add_argument(
        '-r', '--run', action='store_true',
        help='runs scrips following the lifecycle'
    )
    parser.add_argument(
        '-s', '--scripts-path', default='/scripts',
        help='path to scripts folder, default /scripts'
    )
    parser.add_argument(
        '-c', '--cron-path', default='/etc/crontabs/root',
        help='path to scripts folder, default /etc/crontabs/root'
    )

    arguments = parser.parse_args()

    if CRON_BACKUP_SCHEDULE not in os.environ:
        print_logger("Could not find '%s' in the environment variables" % CRON_BACKUP_SCHEDULE)
        exit(1)

    if not croniter.is_valid(os.environ[CRON_BACKUP_SCHEDULE]):
        print_logger("Provided cron schedule '%s' is not valid" % os.environ[CRON_BACKUP_SCHEDULE])
        exit(1)

    # check if provided directory exists
    if not os.path.isdir(arguments.scripts_path):
        print_logger("The following path '%s' is not a valid directory" % arguments.scripts_path)
        exit(1)

    if not arguments.initialize and not arguments.run:
        print_logger("Nothing to do.\nPlease run: 'fridge --help' to see possible options")
        exit(1)

    scripts_detector = ScriptsDetector(arguments.scripts_path)
    scripts_detector.list_detected_scripts()

    if arguments.initialize:
        print_logger("Initializing...")
        start_initialize(scripts_detector, arguments.cron_path)
        print_logger("Initialization complete.")

    if arguments.run:
        print_logger("Running...")
        start_run(scripts_detector)
        print_logger("Finished running.")


if __name__ == '__main__':
    main()
