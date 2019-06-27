import setuptools
from distutils.core import setup

setup(
    name='sidefridge',
    version='0.0.1',
    description='Used to handle backup of applications in same pod',
    author='Andrei Neagu',
    author_email='it.neagu.andrei@gmail.com',
    packages=['sidefridge'],
    install_requires=[
        "croniter"
    ],
    entry_points={
        'console_scripts': [
            'fridge = sidefridge.main:main',
            'kubectlexec = sidefridge.kubectlexec:main',
            'store_var = sidefridge.storage:store_var',
            'load_var = sidefridge.storage:load_var'
        ]
    }
)
