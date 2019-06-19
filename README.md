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

# Kubernetes example

The following is an example on how to configure your sidecar container.

Create a service account which can access your containers inside the pod. 
The following manages the entire namespace, you may already be using something like this in your CI.


    # Used to grant access to all the namespaces
    ---
    kind: Namespace
    apiVersion: v1
    metadata:
      name: example
      labels:
        name: example
    ---
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: example-full-access-service-account
      namespace: example
    
    ---
    kind: Role
    apiVersion: rbac.authorization.k8s.io/v1beta1
    metadata:
      name: example-full-access-role
      namespace: example
    rules:
      - apiGroups: ["", "extensions", "apps"]
        resources: ["*"]
        verbs: ["*"]
      - apiGroups: ["batch"]
        resources:
          - jobs
          - cronjobs
        verbs: ["*"]
    
    ---
    kind: RoleBinding
    apiVersion: rbac.authorization.k8s.io/v1beta1
    metadata:
      name: example-full-access-role-binding
      namespace: example
    subjects:
      - kind: ServiceAccount
        name: example-full-access-service-account
        namespace: example
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: Role
      name: example-full-access-role
 

      
Create your`app.yaml` containing data for the application.

In this example we are using a `mongodb-ambassador` to easily access everything via localhost on port 27017. 
Backup is a trivial task now. 

    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: example-backup-sidecar-config-install
      namespace: example
    data:
      install.sh: |
        #!/bin/bash
        apk add mongodb-tools
      install2.sh: |
        #!/bin/bash
        echo "done installing"
    ---
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: example-backup-sidecar-config-backup
      namespace: example
    data:
      db_backup.sh: |
        #!/bin/bash
        echo "Starting db backup"
        mongodump --db example
        ARCHIVE="example_$(date +"%m_%d_%Y_%H_%M_%S").tar.gz"
        echo $ARCHIVE
        tar -zcvf "$ARCHIVE" dump/

        # Use your favourite tool to upload data somewere in cold storage. install it with 
        # an install script
        
        rm -rf dump/
        rm $ARCHIVE
        echo "Finished backup"
      app_data_backup.sh: |
       #!/bin/bash
       
       echo "Starting data backup"
       # Assuming 'python backup.py --backup-path /backup_directory' will create a backup 
       # of your app's data inside the /backup_direcotry folder, the following command
       # will run inside your TRAGET_CONTAINER and create a backup
       kubectlexec python backup.py --backup-path /backup_directory
       
       # Move to the /backup_directory direcotry mounted inside the backup-sidecar container
       # we are using the same directory name and we should find our backups here 
       cd /backup_directory
       
       # Use your favourite tool to upload data somewere in cold storage. install it with 
       # an install script
        
       # cleanup all the mess you did before 
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: example-deployment
      namespace: example
      labels:
        app: example
    spec:
      selector:
        matchLabels:
          app: example
      template:
        metadata:
          labels:
            app: example
        spec:
          hostname: example
          restartPolicy: Always
          serviceAccountName: example-full-access-service-account
          volumes:
            - name: example-container-shared-data-dir
              emptyDir: {}
            - name: example-backup-sidecar-config-install-volume
              configMap:
                name: example-backup-sidecar-config-install
                defaultMode: 0744
                items:
                  - key: install.sh
                    path: install.sh
                  - key: install2.sh
                    path: install2.sh
            - name: example-backup-sidecar-config-backup-volume
              configMap:
                name: example-backup-sidecar-config-backup
                defaultMode: 0744
                items:
                  - key: db_backup.sh
                    path: db_backup.sh
                  - key: app_data_backup.sh
                    path: app_data_backup.sh
          containers:
            - name: example-app
              image: YOUR_COOL_APP
              volumeMounts:
                - name: example-container-shared-data-dir
                  mountPath: /backup_directory
            - name: mongodb-ambassador
              image: k8s.gcr.io/proxy-to-service:v2
              args: [ "tcp", "27017", "mongodb-service" ]
              ports:
                - name: tcp
                  protocol: TCP
                  containerPort: 27017
                  hostPort: 27017
            - name: backup-sidecar
              image: hubhk/sidefridge
              imagePullPolicy: Always
              volumeMounts:
                - name: example-container-shared-data-dir
                  mountPath: /backup_directory
                - mountPath: /scripts/install_dependencies
                  name: example-backup-sidecar-config-install-volume
                - mountPath: /scripts/backups
                  name: example-backup-sidecar-config-backup-volume
              env:
                - name: CRON_BACKUP_SCHEDULE
                  value: "0 1 1 * *"
                - name: TARGET_CONTAINER
                  value: "example-app"
                - name: POD_NAME
                  valueFrom:
                    fieldRef:
                      fieldPath: metadata.name

# Development

To ease your life during development the following may be useful.

Build image:

    docker build -t sidefridge .

Run image:

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge 

Run shell in container

    docker run --rm -it -e CRON_BACKUP_SCHEDULE="* * * * *" sidefridge /bin/sh
