#!/usr/bin/env python3

__copyright__ = "Copyright (C) 2021 WeZZard"
__license__ = "MIT"

from typing import List, Optional, Union


import os
import datetime
import chardet

from beancount.ingest import importer
from beancount.ingest import cache

from BeanPorter.bpcml.BPCML import BPCML, Importer

from BeanPorter.BeanExtractContext import BeanExtractContext

def _make_converter_with_encoding(encoding: Optional[str]):
  def contents(filename: str):
    """A converter that just reads the entire contents of a file.

    Args:
      num_bytes: The number of bytes to read.
    Returns:
      A converter function.
    """
    # Attempt to detect the input encoding automatically, using chardet and a
    # decent amount of input.
    if encoding is None:
      with open(filename, 'rb') as infile:
          rawdata = infile.read()
      detected = chardet.detect(rawdata)
      detected_encoding = detected['encoding']

    final_encoding = encoding if encoding is not None else detected_encoding

    with open(filename, encoding=final_encoding) as file:
      return file.read()
  return contents


class BeanExtractImporter(importer.ImporterProtocol):
  
  def __init__(self, importer: Importer):
    assert(isinstance(importer, Importer))
    self.importer = importer
  
  def name(self) -> str:
    return self.importer.name

  def identify(self, file: cache._FileMemo) -> bool:
    # Yes, only support csv.
    if file.mimetype() != "text/csv":
      return False

    return self.importer.probe.test(file)
  
  def extract(self, file: cache._FileMemo, existing_entries: Optional[List]=None) -> List:
    converter = _make_converter_with_encoding(self.importer.encoding)
    normalized_file_contents = self.importer.normalize(file.convert(converter))

    entries = list()

    # Returns empty entries when no real contents
    if len(normalized_file_contents) <= 1:
      return entries

    normalized_file_header = normalized_file_contents[0]
    normalized_file__body = normalized_file_contents[1:]

    extract_context = BeanExtractContext(
      self.FLAG,
      self.importer, 
      normalized_file_header
    )

    for each_row in normalized_file__body:
      txn = extract_context.evaluate(each_row, self.FLAG)
      if txn is not None:
        entries.append(txn)

    return entries
  
  def file_date(self, file: cache._FileMemo) -> Optional[datetime.date]:
    pass

  @staticmethod
  def make_importers(config_files: Optional[Union[str, List[str]]]) -> List['BeanExtractImporter']:
    """
    Makes importers from .bean_porter_config.yaml and user config files.

    Disabled importers would not be returned.

    """
    module_dir = os.path.dirname(os.path.abspath(__file__))

    root_config_file = os.path.join(module_dir, 'bean_porter_config.yaml')

    root_config = BPCML.make_with_serialization_at_path(root_config_file)

    if root_config is None:
      return list()

    paths = []

    if isinstance(config_files, str):
      paths.append(config_files)
    if isinstance(config_files, list):
      paths.extend(config_files)

    user_config_files = list(filter(lambda x : x is not None, [BPCML.make_with_serialization_at_path(p) for p in paths]))

    for each_user_config in user_config_files:
      root_config.extend_with_config(each_user_config)

    root_config.resolve()

    enabled_importers = filter(lambda i : i.name not in root_config.disabled_importers, root_config.importers)
    
    return [BeanExtractImporter(i) for i in enabled_importers]
