# sidefridge

### Configuration

Use environment variables to configure this container as a sidecar for backup.

- **CRON_BACKUP_SCHEDULE** configuration
- **TARGET_CONTAINER** specify the k8s container name in which commands must be run
- **POD_NAME** must defile an environment variable containing the pod's name.

Use the following:
    
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name

refer to [Expose Pod Information to Containers Through Environment 
Variables](https://kubernetes.io/docs/tasks/inject-data-application/environment-variable-expose-pod-information/#use-pod-fields-as-values-for-environment-variables):

### Scripting extras

To execute commands in a target container inside the same pod use `kubectlexec` command 
followed by the command you want to run. For example

    kubectlexec npm run backup


### Lifecycle hooks

Hooks are `bash` or `sh` scripts which are started at given moments in the app's lifecycle.

Available hooks:

- **install_dependencies** installs dependencies via `apk`
- **backups** (runs as scheduled by the cronjob)
- **before_backups** (called before all backup scripts)
- **after_backups** (called after all backup scripts)
- **on_error** (if an error occurs, exit code different then 0, this is invoked, it will not trigger on error once again)

Hooks directory structure:

    /scripts
        - install_dependencies/
        - backups/
        - before_backups/
        - after_backups/
        - on_error/

Base script example 1:

    #!/bin/sh
    
    echo "Hellow world"
    
Base script example 2:

    #!/bin/bash
    
    echo "Hellow world"         


Cron is used to schedule backups which will run locally in the container environment.

Should have a service responsible for showing the details of operations and if the backups went ok (exit codes)


Create a directory called “/scripts” where all scripts need to be mounted, and where all scripts are executed


### CRON

Run a process to configure cron from enviornment variables set on the contaienr

start the python script which watches for schedules, start cronjob, maybe only cron is sufficient


# Example command

Run this for development:

    clear && CRON_BACKUP_SCHEDULE="* * * * *" fridge -i -r -c cronjob -s example_scripts
    
    
# Docker

Build image

    docker build -t sidefridge .

Run image:

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge 

Run shell in container

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge /bin/sh
