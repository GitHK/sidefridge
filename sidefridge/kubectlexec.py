import os
import sys

from sidefridge.utils import print_logger

TARGET_CONTAINER = "TARGET_CONTAINER"
POD_NAME = "POD_NAME"


def run_in_container(command):
    """
    Will execute a given command in a container like `ls -la`
    """

    # subprocess was replaced, had issues with this; output is no longer steamed :\
    kubectl_command = 'kubectl exec -it {pod} -c {container} -- /bin/sh -c "{command}"'.format(
        pod=os.environ[POD_NAME],
        container=os.environ[TARGET_CONTAINER],
        command=command
    )

    os.system(kubectl_command)


def main():
    if TARGET_CONTAINER not in os.environ:
        print_logger("Could not find '%s' in the environment variables" % TARGET_CONTAINER)
        exit(1)

    if POD_NAME not in os.environ:
        print_logger("Could not find '%s' in the environment variables" % POD_NAME)
        exit(1)

    cli_arguments = sys.argv[1:]

    if len(cli_arguments) < 1:
        print_logger("You must provide a command to be executed in the target container")
        exit(1)

    command = " ".join(cli_arguments)
    run_in_container(command)


if __name__ == '__main__':
    main()
