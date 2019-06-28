import argparse
import os
from collections import deque
from jinja2 import Template

from sidefridge.scripts import ScriptsDetector, SUPPORTED_DIRECTORIES
from sidefridge.utils import print_logger

TEMPLATE_DIRECTORY_CONFIG_MAP = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{project_name}}-{{container_name}}-config-{{hook_name}}
  namespace: {{namespace}}
data:
{% for file_name in content_data['file_names'] -%}
{{ file_name | indent(2, True) }}: |
{% for line in content_data['file_content'][file_name] -%}
{{ line | indent(4, True) }}
{%- endfor %}
{%endfor %}
"""[1:-1]  # strip first and last '\n'

TEMPLATE_SERVICE_ACCOUNT_NAMES_VOLUMES_PARTIAL = """
serviceAccountName: {{project_name}}-full-access-service-account
volumes:
{% for hook_name in hooks_data -%}
  {{ ("- name: {project_name}-{container_name}-config-{hook_name}-volume".format(project_name=project_name, container_name=container_name, hook_name=hook_name)) | indent(2, True) }}
    configMap:
      name: {{project_name}}-{{container_name}}-config-{{hook_name}}
      defaultMode: 0744
      items:
{% for script in hooks_data[hook_name] -%}
{{ ("- key: %s" % script) | indent(8, True) }}
{{ ("  path: %s" % script) | indent(8, True) }}
{% endfor %}
{%- endfor %}
"""[1:-1]  # strip first and last '\n'

TEMPLATE_VOLUME_MOUNTS_PARTIAL = """
volumeMounts:
{% for script_path, hook_name in content_data -%}
{{"- mountPath: {script_path}".format(script_path=script_path) | indent(2, True)}}
{{"  name: {project_name}-{container_name}-config-{hook_name}-volume".format(project_name=project_name, container_name=container_name, hook_name=hook_name) | indent(2, True)}}
{% endfor %}
"""[1:-1]  # strip first and last '\n'

TEMPLATE_SERVICE_ACCOUNT_ROLE_ROLE_BINDING = """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{project_name}}-full-access-service-account
  namespace: {{namespace}}
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: {{project_name}}-full-access-role
  namespace: {{namespace}}
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
  name: {{project_name}}-full-access-role-binding
  namespace: {{namespace}}
subjects:
  - kind: ServiceAccount
    name: {{project_name}}-full-access-service-account
    namespace: {{namespace}}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{project_name}}-full-access-role
"""[1:-1]  # strip first and last '\n'


def render_template(template, values):
    template = Template(template)
    return template.render(**values)


def render_config_map(namespace, project_name, container_name, hook_name, content_data):
    return render_template(
        template=TEMPLATE_DIRECTORY_CONFIG_MAP,
        values=dict(
            namespace=namespace,
            project_name=project_name,
            container_name=container_name,
            hook_name=hook_name,
            content_data=content_data
        )
    )


def render_service_account_name_volumes_partial(scripts_detector, namespace, project_name, container_name):
    hooks_data = dict()

    for hook_name in SUPPORTED_DIRECTORIES:
        hooks_data[hook_name] = []
        for file_path in getattr(scripts_detector, hook_name, []):
            key = get_script_name_from_path(file_path, hook_name)
            hooks_data[hook_name].append(key)

    return render_template(
        template=TEMPLATE_SERVICE_ACCOUNT_NAMES_VOLUMES_PARTIAL,
        values=dict(
            namespace=namespace,
            project_name=project_name,
            container_name=container_name,
            hooks_data=hooks_data,
        )
    )


def render_volume_mounts_partial(namespace, project_name, container_name, container_scripts_path):
    content_data = []

    for hook_name in SUPPORTED_DIRECTORIES:
        script_path = os.path.join(container_scripts_path, hook_name)
        content_data.append((script_path, hook_name))

    return render_template(
        template=TEMPLATE_VOLUME_MOUNTS_PARTIAL,
        values=dict(
            namespace=namespace,
            project_name=project_name,
            container_name=container_name,
            content_data=content_data,
        )
    )


def get_file_content(file_path):
    file_content = deque()
    with open(file_path, 'r') as f:
        for line in f:
            file_content.append(line)

    return file_content


def get_script_name_from_path(file_path, hook_name):
    return file_path.split(hook_name)[-1][1:]


def generate_config_map_for_hook(scripts_detector, namespace, project_name, container_name, hook_name):
    content_data = dict(file_names=[], file_content={})
    for file_path in getattr(scripts_detector, hook_name, []):
        key = get_script_name_from_path(file_path, hook_name)
        content_data['file_names'].append(key)
        content_data['file_content'][key] = get_file_content(file_path)

    rendered_template = render_config_map(
        namespace=namespace,
        project_name=project_name,
        container_name=container_name,
        hook_name=hook_name,
        content_data=content_data
    )
    return rendered_template


def assemble_config_yaml(scripts_detector, namespace, project_name, container_name, output_path):
    results = []

    for hook_name in SUPPORTED_DIRECTORIES:
        hook_config_yaml = generate_config_map_for_hook(
            scripts_detector=scripts_detector,
            namespace=namespace,
            project_name=project_name,
            container_name=container_name,
            hook_name=hook_name
        )
        results.append(hook_config_yaml)

    file_content = "---\n".join(results)

    with open(os.path.join(output_path, '%s-config-maps.yaml' % project_name), 'w') as f:
        f.write(file_content)


def assemble_service_account_name_volumes_partial(scripts_detector, namespace, project_name, container_name, output_path):
    rendered_yaml = render_service_account_name_volumes_partial(
        scripts_detector=scripts_detector,
        namespace=namespace,
        project_name=project_name,
        container_name=container_name
    )

    with open(os.path.join(output_path, '%s-partial_service_account_name_volumes.yaml' % project_name), 'w') as f:
        f.write(rendered_yaml)


def assemble_volume_mounts_partial(namespace, project_name, container_name, output_path, container_scripts_path):
    rendered_yaml = render_volume_mounts_partial(
        namespace=namespace,
        project_name=project_name,
        container_name=container_name,
        container_scripts_path=container_scripts_path
    )

    with open(os.path.join(output_path, '%s-partial_volume_mounts.yaml' % project_name), 'w') as f:
        f.write(rendered_yaml)


def assemble_service_account_role_role_binding(namespace, project_name, output_path):
    rendered_yaml = render_template(
        template=TEMPLATE_SERVICE_ACCOUNT_ROLE_ROLE_BINDING,
        values=dict(
            namespace=namespace,
            project_name=project_name,
        )
    )
    with open(os.path.join(output_path, '%s-accounts.yaml' % project_name), 'w') as f:
        f.write(rendered_yaml)


def main():
    """ Generates all needed configurations for k8s after providing a scripts directory and some other parameters """

    parser = argparse.ArgumentParser(
        description='Tool for running and initializing backup container'
    )
    parser.add_argument(
        'namespace', type=str,
        help='the k8s namespace'
    )
    parser.add_argument(
        'project_name', type=str,
        help='the current project name'
    )
    parser.add_argument(
        'container_name', type=str,
        help='container name where volumeMounts and volumes are to be used'
    )
    parser.add_argument(
        'in_dir', type=str,
        help='path to your directory containing the hooks'
    )
    parser.add_argument(
        'out_dir', type=str,
        help='directory for k8s configuration file output'
    )
    parser.add_argument(
        '-csp', '--container-scripts-path', default='/scripts',
        help='path to scripts folder inside the container, default /scripts'
    )

    arguments = parser.parse_args()

    # check if provided directory exists
    if not os.path.isdir(arguments.in_dir):
        print_logger("The following path '%s' is not a valid directory" % arguments.in_dir)
        exit(1)

    # check if provided directory exists
    if not os.path.isdir(arguments.out_dir):
        print_logger("The following path '%s' is not a valid directory" % arguments.out_dir)
        exit(1)

    scripts_detector = ScriptsDetector(arguments.in_dir)

    # store yaml files in output directory

    assemble_config_yaml(
        scripts_detector=scripts_detector,
        namespace=arguments.namespace,
        project_name=arguments.project_name,
        container_name=arguments.container_name,
        output_path=arguments.out_dir
    )

    assemble_service_account_name_volumes_partial(
        scripts_detector=scripts_detector,
        namespace=arguments.namespace,
        project_name=arguments.project_name,
        container_name=arguments.container_name,
        output_path=arguments.out_dir
    )

    assemble_volume_mounts_partial(
        namespace=arguments.namespace,
        project_name=arguments.project_name,
        container_name=arguments.container_name,
        output_path=arguments.out_dir,
        container_scripts_path=arguments.container_scripts_path
    )

    assemble_service_account_role_role_binding(
        namespace=arguments.namespace,
        project_name=arguments.project_name,
        output_path=arguments.out_dir
    )


if __name__ == '__main__':
    main()
