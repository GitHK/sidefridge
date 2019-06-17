import os
import subprocess
import sys

from sidefridge.utils import print_logger

TARGET_CONTAINER = "TARGET_CONTAINER"
POD_NAME = "POD_NAME"


def run_command(command):
    """ Run commands on host """
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.write(c.decode('utf-8'))

    process.communicate()


def run_in_container(command):
    """
    Will execute a given command in a container like `ls -la`
    """
    kubectl_command = "kubectl exec -it {pod} -c {container} {command}".format(
        pod=os.environ["POD_NAME"],
        container=os.environ["PARENT_CONTAINER"],
        command=command
    )

    run_command(kubectl_command)


def main():
    if TARGET_CONTAINER not in os.environ:
        print_logger("Could not find '%s' in the environment variables" % TARGET_CONTAINER)
        exit(1)

    if POD_NAME not in os.environ:
        print_logger("Could not find '%s' in the environment variables" % POD_NAME)
        exit(1)

    run_command("ls -la")


if __name__ == '__main__':
    main()
