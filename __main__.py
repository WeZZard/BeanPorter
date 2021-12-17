#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import argparse

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

sys.path.append(".")

from beancount.ingest.extract import extract

from BeanExtractImporter import BeanExtractImporter

parser = argparse.ArgumentParser()

parser.add_argument(
  "--file",
  type=str,
  help="Bill file name.")

parser.add_argument(
  "--config",
  type=str,
  nargs='?',
  action='append',
  default=None,
  help="Config file names. Multiple config file is allowed.")

parser.add_argument(
  "--ascending",
  type=bool,
  nargs='?',
  default=True,
  help="Ordering.")

args = parser.parse_args()

if __name__ == '__main__':
  extract(
    BeanExtractImporter.make_importers(args.config), 
    [args.file],
    sys.stdout,
    entries=None,
    options_map=None,
    mindate=None,
    ascending=args.ascending,
    hooks=None)
