#!/usr/bin/env python3

from setuptools import setup, find_packages

install_requires = [
  'beancount',
  'pyyaml',
]

setup(
  name="BeanPorter",
  version='0.1',
  description="Beancount importer",
  long_description=
  """
  Beancount importer.
  """,
  license="MIT",
  author="WeZZard",
  author_email="me@wezzard.com",
  url="https://github.com/WeZZard/BeanPorter",
  download_url="https://github.com/WeZZard/BeanPorter",
  packages=find_packages(where='src'),
  package_dir={
    "BeanPorter": "src/BeanPorter",
    "BeanPorter.bpcml": "src/BeanPorter/bpcml",
  },
  install_requires = install_requires,
  package_data={
    'BeanPorter': ['bean_porter_config.yaml']
  },
  entry_points = {'console_scripts': ['bean-porter=BeanPorter:main']},
  python_requires='>=3.6',
)
