#!/usr/bin/env python3

from setuptools import setup, find_packages

install_requires = [
    'beancount',
    'pyyaml',
]

setup(name="BeanPorter",
      version='0.1',
      description="Beancount importer",
      long_description=
      """
      Beancount importer.
      """,

      license="GNU GPLv2 only",
      author="WeZZard",
      author_email="me@wezzard.com",
      url="https://github.com/WeZZard/BeanPorter",
      download_url="https://github.com/WeZZard/BeanPorter",
      packages=find_packages(exclude=['experiments*']),
      install_requires = install_requires,
      package_data={
        'BeanPorter': ['bean_extract_config.yaml']
      },
      entry_points = {'console_scripts': ['bean-porter=BeanPorter:main']},
      python_requires='>=3.6',
)
