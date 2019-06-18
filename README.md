# sidefridge

A kubernetes sidecar backup container. Manage dependencies and backups via bash or sh scripts.

## Getting started

There are a couple of configurations which need to be met in order to have a working backup container:

- define environment variables: cron schedule, pod name and target container
- define hooks: install script and backup script


### Environment

The following variables are mandatory:

- **CRON_BACKUP_SCHEDULE** configure cron job schedule
- **TARGET_CONTAINER** specify the kubernetes container name in which commands must be run
- **POD_NAME** must defile an environment variable containing the pod's name

Use the following:
    
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name

refer to [Expose Pod Information to Containers Through Environment 
Variables](https://kubernetes.io/docs/tasks/inject-data-application/environment-variable-expose-pod-information/#use-pod-fields-as-values-for-environment-variables):

Full env configuration example, runs backup every minute:

    env:
    - name: CRON_BACKUP_SCHEDULE
      value: "* * * * *"
    - name: TARGET_CONTAINER
      value: "example-production-app"
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name


### Lifecycle hooks

Hooks are `bash` or `sh` scripts which are triggered at given moments in the app's lifecycle.

Available hooks:

- **install_dependencies** installs dependencies via `apk`
- **backups** (runs as scheduled by the cronjob)
- **before_backups** (called before all backup scripts)
- **after_backups** (called after all backup scripts)
- **on_error** (if an error occurs, exit code different then 0, this is invoked, it will not trigger on error once again)

The container expects all hooks to be placed inside the `/scripts` directory with a structure similar to the following:

    /scripts
      install_dependencies/
        install1.sh
        install2.sh
      backups/
        bkp1.sh
        bkp2.sh
      before_backups/
        before_backup.sh
      after_backups/
        after_bkup.sh
      on_error/
        errorz.sh

Script names do not matter, all available files are interpreted as scripts. If multiple scripts are
defined under the same hook, lexicographic ordering is used to determine execution order.

**Examples**

The following install script named `install.sh` will install mongodb to have access to the mongodump utility:

    #!/bin/sh
    
    apk add mongodb
    
    
it must be placed in the following path: `/scripts/install_dependencies/install.sh`

    
To backup the database simply define a `bkp` script like this one:

    #!/bin/bash
    
    mongodump --out /data/backup/
    
it must be placed in the following path: `/scripts/backups/bkp`


### Scripting extras

To execute commands in a TARGET_CONTAINER inside the same pod use `kubectlexec` command in your scripts
followed by the command you want to run. For example, if you need to run `python backup.py`in TARGET_CONTAINER:

    kubectlexec python backup.py

The command will be executed via kubectl in the specified container from this container.


# Development

To ease your life during development the following may be useful.

Build image:

    docker build -t sidefridge .

Run image:

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge 

Run shell in container

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge /bin/sh
