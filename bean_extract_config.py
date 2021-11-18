#!/usr/bin/env python3

import yaml
import jsonpickle # For testing
import os
import typing
from typing import List
from typing import Dict
from typing import Optional

_DEFAULT_IMPORTER_COUNTER = 0

def make_default_impoter_name() -> str:
  global _DEFAULT_IMPORTER_COUNTER
  if _DEFAULT_IMPORTER_COUNTER == 0:
    name = 'Default'
  else:
    name = 'Default-{c}'.format(c=(_DEFAULT_IMPORTER_COUNTER))
  _DEFAULT_IMPORTER_COUNTER += 1
  return name

class Developer:

  def __init__(self, is_debug_enabled: bool = False):
    self.is_debug_enabled = is_debug_enabled

  @staticmethod
  def make_with_serialization(serialization):
    if serialization['debug'] is not None:
      is_debug_enabled = serialization['debug'] == True
    else:
      is_debug_enabled = False
    
    return Developer(is_debug_enabled=is_debug_enabled)

class Probe:

  @staticmethod
  def make_with_serialization(serialization) -> 'Probe':
    if serialization is None:
      return _NoProbe()
    
    return _FileNameProbe.make_with_serialization(serialization)

class _NoProbe(Probe):
  pass

class _FileNameProbe(Probe):

  @staticmethod
  def make_with_serialization(serialization) -> '_FileNameProbe':
    return _FileNameProbe(serialization['file_name'])
  
  def __init__(self, file_name: str):
    assert isinstance(file_name, str), 'file_name is {}'.format(type(file_name))
    self.file_name = file_name

class TableHeader:
  
  @staticmethod
  def make_with_serialization(serialization) -> 'TableHeader':
    if serialization is None:
      return _NoTableHeader()
    
    return _LineSpecifiedTableHeader.make_with_serialization(serialization)

class _NoTableHeader(TableHeader):
  pass

class _LineSpecifiedTableHeader(TableHeader):

  @staticmethod
  def make_with_serialization(serialization) -> '_LineSpecifiedTableHeader':
    return _LineSpecifiedTableHeader(serialization['line'])
  
  def __init__(self, line):
    assert isinstance(line, int)
    self.line = line

class Stripper:
  
  @staticmethod
  def make_strippers_with_serialization(serialization) -> List['Stripper']:
    if serialization is None:
      return list()

    strippers = list()
    for action_name in serialization:
      action_value = serialization[action_name]
      strippers.append(Stripper.make_with_action(action_name, action_value))
    
    return strippers
  
  @staticmethod
  def make_with_action(action_name, action_value) -> 'Stripper':
    assert isinstance(action_name, str)

    if action_name == 'remove_first':
      assert isinstance(action_value, int)
      return _RemoveFirstKStripper(action_value)

    if action_name == 'remove_last':
      assert isinstance(action_value, int)
      return _RemoveLastKStripper(action_value)

    if action_name == 'remove_before':
      assert isinstance(action_value, str)
      return _RemoveBeforePatternStripper(action_value, False)

    if action_name == 'remove_after':
      assert isinstance(action_value, str)
      return _RemoveAfterPatternStripper(action_value, False)

    if action_name == 'remove_before_and_include':
      assert isinstance(action_value, str)
      return _RemoveBeforePatternStripper(action_value, True)

    if action_name == 'remove_after_and_include':
      assert isinstance(action_value, str)
      return _RemoveAfterPatternStripper(action_value, True)
    
    raise AssertionError('Unrecognized stripper action name: {}'.format(action_name))
  

class _RemoveFirstKStripper(Stripper):
  
  def __init__(self, k: int):
    self.k = k


class _RemoveLastKStripper(Stripper):

  def __init__(self, k: int):
    self.k = k


class _RemoveBeforePatternStripper(Stripper):

  def __init__(self, pattern: str, includes: bool):
    self.pattern = pattern
    self.includes = includes


class _RemoveAfterPatternStripper(Stripper):

  def __init__(self, pattern: str, includes: bool):
    self.pattern = pattern
    self.includes = includes

class Transformer:
  
  @staticmethod
  def make_transformers_with_serialization(serialization) -> List['Transformer']:
    if not isinstance(serialization, list):
      return list()
    
    return [Transformer.make_with_serialization(c) for c in serialization]
  
  @staticmethod
  def make_with_serialization(serialization) -> 'Transformer':
    if serialization is None:
      return Transformer('Unnamed Transformer', None, None)

    name = serialization.get('name', 'Unnamed Transformer')
    assert isinstance(name, str), 'name is {} in {}'.format(name, serialization)

    patterns = serialization.get('patterns', dict())
    if patterns is None:
      patterns = dict()
    assert isinstance(patterns, dict), 'patterns is {} in {}'.format(patterns, serialization)

    results = serialization.get('results', dict())
    assert isinstance(results, dict), 'results is {} in {}'.format(results, serialization)

    return Transformer(name, patterns, results)
  
  def __init__(self, name: str, patterns: Optional[Dict], results: Optional[Dict]):
    assert isinstance(name, str)
    assert patterns is None or isinstance(patterns, dict)
    assert results is None or isinstance(results, dict)
    self.name = name
    self.patterns = patterns
    self.results = results


class Importer:

  @staticmethod
  def make_importers(config) -> List['Importer']:
    if not isinstance(config, list):
      return list()

    return [Importer.make_importer(x) for x in config]

  @staticmethod
  def make_importer(config) -> 'Importer':
    assert config is not None
    
    name = config.get('name', None)

    probe = Probe.make_with_serialization(config.get('probe'))
    table_header = TableHeader.make_with_serialization(config.get('table_header'))
    strippers = Stripper.make_strippers_with_serialization(config.get('strippers'))
    terminology_map = config.get('terminology_map', dict())
    transformers = Transformer.make_transformers_with_serialization(config.get('transformers'))

    return Importer(
      name, 
      probe, 
      table_header, 
      strippers, 
      terminology_map, 
      transformers
    )
  
  def __init__(
    self, 
    name: Optional[str], 
    probe: Probe, 
    table_header: TableHeader, 
    strippers: List[Stripper], 
    terminology_map: Dict, 
    transformers: List[Transformer]
  ):
    self.name = name if name is not None else make_default_impoter_name()
    self.probe = probe
    self.table_header = table_header
    self.strippers = strippers
    self.terminology_map = terminology_map
    self.transformers = transformers
  
  def extend_with_extension(self, extension: 'ImporterExtension'):
    assert isinstance(extension, ImporterExtension)
    assert self.name == extension.name
    if extension.probe is not None:
      print('Importer extension may not have probe.')
      print('Probe: {}'.format(extension.probe))
    if extension.table_header is not None:
      print('Importer extension may not have table header.')
      print('Table header: {}'.format(extension.table_header))
    self.strippers.extend(extension.strippers)
    self.terminology_map.update(extension.terminology_map)
    self.transformers.extend(extension.transformers)


class ImporterExtension(Importer):

  @staticmethod
  def make_importers_with_serialization(serialization) -> List['ImporterExtension']:
    assert isinstance(serialization, list), "{}".format(serialization)
    return [ImporterExtension.make_with_serialization(c) for c in serialization]

  @staticmethod
  def make_with_serialization(serialization, extracted_name: Optional[str] = None) -> 'ImporterExtension':
    assert serialization is not None
    
    name = serialization.get('name')
    if name is None and extracted_name is not None:
      name = extracted_name
    assert name is not None, 'Importer extension may have a name.'
    assert isinstance(name, str)
    probe = Probe.make_with_serialization(serialization.get('probe'))
    table_header = TableHeader.make_with_serialization(serialization.get('table_header'))
    strippers = Stripper.make_strippers_with_serialization(serialization.get('strippers'))
    terminology_map = serialization.get('terminology_map', dict())
    transformers = Transformer.make_transformers_with_serialization(serialization.get('transformers'))

    return ImporterExtension(
      name, 
      probe, 
      table_header, 
      strippers, 
      terminology_map, 
      transformers
    )

  @staticmethod
  def make_named_importer_extensions_from_serialization(serialization) -> List['ImporterExtension']:
    assert isinstance(serialization, dict)
    extensions = list()
    for key in serialization:
      if key.startswith('extends_'):
        name = key.removeprefix('extends_')
        extension = ImporterExtension.make_with_serialization(serialization[key], extracted_name=name)
        extensions.append(extension)
    return extensions


class Config:

  @staticmethod
  def make_with_serialization_at_path(path: str) -> Optional['Config']:
    try:
      with open(path, 'r') as config_file:
        serialization = yaml.safe_load(config_file)
      config = Config.make_with_serialization(serialization)
      config.cwd = os.path.dirname(path)
      config.path = path
      return config
    except Exception:
      return None

  @staticmethod
  def make_with_serialization(serialization: Optional[Dict]) -> 'Config':
    if serialization is not None:
      developer = Developer.make_with_serialization(serialization.get('developer'))
      disabled_importers_list = serialization.get('disabled_importers', list())
      include_list = serialization.get('include', list())
      importers = Importer.make_importers(serialization.get('importers', list()))
      importer_extensions = ImporterExtension.make_importers_with_serialization(serialization.get('extensions', list()))
      named_impoter_extensions = ImporterExtension.make_named_importer_extensions_from_serialization(serialization)
      importer_extensions.extend(named_impoter_extensions)
    else:
      developer = Developer()
      disabled_importers_list = list()
      include_list = list()
      importers = list()
      importer_extensions = list()
    
    return Config(developer, disabled_importers_list, include_list, importers, importer_extensions)

  def __init__(
    self, 
    developer: Developer, 
    disabled_importers_list: List, 
    include_list: List, 
    importers: List[Importer], 
    importer_extensions: List[ImporterExtension]
  ):
    self.developer = developer
    self.disabled_importers_list = disabled_importers_list
    self.include_list = include_list
    self.importers = importers
    self.importer_extensions = importer_extensions
  
  def resolve(self):
    # Resolves the config. Extends the config's contents with include lists 
    # and importer extensions.

    cwd = self.cwd

    if cwd is None:
      return
    
    for each_include in self.include_list:
      full_include_path = os.path.join(cwd, each_include)
      included_config = Config.make_with_serialization_at_path(full_include_path)
      if included_config is not None:
        self.extend_with_config(included_config)
    
    del self.include_list

    for each_importer_extension in self.importer_extensions:
      for each_importer in self.importers:
        if each_importer.name == each_importer_extension.name:
          each_importer.extend_with_extension(each_importer_extension)
    
    del self.importer_extensions

  def extend_with_config(self, config: 'Config'):
    if config == self:
      return
    
    # Resolve the given config firstly. Thus we don't have to process configs
    # referred by its include-lists.
    config.resolve()

    self.disabled_importers_list.extend(config.disabled_importers_list)

    for each_importer in config.importers:
      existed_importer = next(filter(lambda i: i.name == each_importer.name, self.importers), None)
      if existed_importer is not None:
        print('Importer with name \"{name}\" have already been there in config at path: {path}'.format(name=each_importer.name, path=self.path))
        continue
      self.importers.append(each_importer)

    for each_importer_extension in config.importer_extensions:
      for each_importer in self.importers:
        if each_importer.name == each_importer_extension.name:
          each_importer.extend_with_extension(each_importer_extension)


def main():

  global cwd

  cwd = os.getcwd()

  config_file_path = os.path.join(cwd, '.bean_extract_config.yaml')

  config = Config.make_with_serialization_at_path(config_file_path)
  config.resolve()
  reserialized_config = jsonpickle.encode(config)

  print(yaml.dump(yaml.load(reserialized_config, Loader=yaml.Loader), indent=2))

if __name__ == '__main__':
  main()
