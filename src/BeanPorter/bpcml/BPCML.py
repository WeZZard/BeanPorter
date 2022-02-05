#!/usr/bin/env python3

from abc import abstractmethod

from typing import List, Dict, Set, Optional

import io
import yaml
import csv
import re
import os
import logging

from BeanPorter.bpcml.ASTContext import ASTContext
from BeanPorter.bpcml.Tokenizer import Tokenizer
from BeanPorter.bpcml.Decls import RuleDecl

from beancount.ingest import cache


_DEFAULT_IMPORTER_COUNTER = 0

REQUIRED_TRANSACTION_PROPERTY_KEYS: Set[str] = frozenset([
  'transaction_name',
  'timestamp',
  'complete',
])

OPTIONAL_TRANSACTION_PROPERTY_KEYS: Set[str] = frozenset([
  'payee',
  'time',
  'debit_account',
  'debit_amount',
  'debit_currency',
  'debit_cost',
  'debit_price',
  'credit_account',
  'credit_amount',
  'credit_currency',
  'credit_cost',
  'credit_price',
  'tag',
  'links',
])

TRANSACTION_PROPERTY_KEYS: Set[str] = frozenset().union(*[REQUIRED_TRANSACTION_PROPERTY_KEYS, OPTIONAL_TRANSACTION_PROPERTY_KEYS])

def make_default_impoter_name() -> str:
  global _DEFAULT_IMPORTER_COUNTER
  if _DEFAULT_IMPORTER_COUNTER == 0:
    name = 'Default'
  else:
    name = 'Default-{c}'.format(c=(_DEFAULT_IMPORTER_COUNTER))
  _DEFAULT_IMPORTER_COUNTER += 1
  return name


def strip_blank(contents):
  """ 
  strip the redundant blank in file contents.
  """
  with io.StringIO(contents) as csvfile:
    csvreader = csv.reader(csvfile, delimiter=",", quotechar='"')
    rows = []
    for row in csvreader:
      rows.append(",".join(['"{}"'.format(x.strip()) for x in row]))
    return "\n".join(rows)

class Developer:

  def __init__(self, is_debug_enabled: bool = False):
    self.is_debug_enabled = is_debug_enabled

  @staticmethod
  def make_with_serialization(serialization) -> Optional['Developer']:
    if serialization is None:
      return None
    
    if serialization['debug'] is not None:
      is_debug_enabled = serialization['debug'] == True
    else:
      is_debug_enabled = False
    
    return Developer(is_debug_enabled=is_debug_enabled)


class FileNameProbe:
  
  @staticmethod
  def make_with_serialization(serialization) -> Optional['FileNameProbe']:
    if serialization is None:
      return None
    
    probe: Optional['FileNameProbe'] = None
    
    pattern = serialization.get('pattern')
    if pattern is not None:
      re_pattern = re.compile(re.escape(pattern))
      probe = _FileNamePatternProbe(re_pattern)
    
    prefix = serialization.get('prefix')
    if prefix is not None:
      if probe is not None:
        raise AssertionError("A probe may have only one kind of configuration for file_name! There have been {}".format(probe.kind()))
      assert(isinstance(prefix, str))
      probe = _FileNamePrefixProbe(prefix)
    
    suffix = serialization.get('suffix')
    if suffix is not None:
      assert(probe is None, "A probe may have only one kind of configuration for file_name! There have been {}".format(probe.kind()))
      assert(isinstance(suffix, str))
      probe = _FileNameSuffixProbe(suffix)
    
    return probe

  @abstractmethod
  def kind(self) -> str:
    pass


class _FileNamePatternProbe(FileNameProbe):

  def __init__(self, re_file_name_pattern: re.Pattern):
    assert(isinstance(re_file_name_pattern, re.Pattern))
    self.pattern = re_file_name_pattern
  
  def kind(self) -> str:
    return 'pattern'
  
  def test(self, file_name: str) -> bool:
    return self.pattern.match(file_name) is not None


class _FileNamePrefixProbe(FileNameProbe):

  def __init__(self, prefix: str):
    assert(isinstance(prefix, str))
    self.prefix = prefix
  
  def kind(self) -> str:
    return 'prefix'
  
  def test(self, file_name: str) -> bool:
    last_component = os.path.basename(os.path.normpath(file_name))
    return last_component.startswith(self.prefix)


class _FileNameSuffixProbe(FileNameProbe):

  def __init__(self, suffix: str):
    assert(isinstance(suffix, str))
    self.suffix = suffix
  
  def kind() -> str:
    return 'suffix'
  
  def test(self, file_name: str) -> bool:
    return file_name.endswith(self.suffix)


class Probe:

  @staticmethod
  def make_with_serialization(serialization) -> 'Probe':
    if serialization is None:
      return _NoProbe()
    
    return _HasProbe(
      FileNameProbe.make_with_serialization(serialization.get('file_name'))
    )
  
  @abstractmethod
  def test(self, file: cache._FileMemo) -> bool:
    pass

class _NoProbe(Probe):
  
  def test(self, file: cache._FileMemo) -> bool:
    return True


class _HasProbe(Probe):

  def __init__(self, file_name_probe: Optional[FileNameProbe]):
    self.file_name_probe = file_name_probe
  
  def test(self, file: cache._FileMemo) -> bool:
    is_file_name_matched = True
    
    if self.file_name_probe is not None:
      is_file_name_matched = self.file_name_probe.test(file.name)
    
    return is_file_name_matched


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
    assert(isinstance(line, int))
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
    assert(isinstance(action_name, str))

    if action_name == 'remove_first':
      assert(isinstance(action_value, int))
      return _RemoveFirstKStripper(action_value)

    if action_name == 'remove_last':
      assert(isinstance(action_value, int))
      return _RemoveLastKStripper(action_value)

    if action_name == 'remove_before':
      assert(isinstance(action_value, str))
      return _RemoveBeforePatternStripper(action_value, False)

    if action_name == 'remove_after':
      assert(isinstance(action_value, str))
      return _RemoveAfterPatternStripper(action_value, False)

    if action_name == 'remove_before_and_include':
      assert(isinstance(action_value, str))
      return _RemoveBeforePatternStripper(action_value, True)

    if action_name == 'remove_after_and_include':
      assert(isinstance(action_value, str))
      return _RemoveAfterPatternStripper(action_value, True)
    
    raise AssertionError('Unrecognized stripper action name: {}'.format(action_name))
  
  @abstractmethod
  def evaluate_in_file_contents(self, file_contents) -> Optional[int]:
    pass

  @abstractmethod
  def is_leading_stripper(self) -> bool:
    pass

  @abstractmethod
  def is_trailing_stripper(self) -> bool:
    pass


class _RemoveFirstKStripper(Stripper):
  
  def __init__(self, k: int):
    self.k = k
  
  def evaluate_in_file_contents(self, file_contents) -> Optional[int]:
    reader = csv.reader(io.StringIO(strip_blank(file_contents)))
    lines_count = sum(1 for _ in reader)

    if lines_count < self.k:
      return lines_count
    
    return self.k

  def is_leading_stripper(self) -> bool:
    return True

  @abstractmethod
  def is_trailing_stripper(self) -> bool:
    return False


class _RemoveLastKStripper(Stripper):

  def __init__(self, k: int):
    self.k = k
  
  def evaluate_in_file_contents(self, file_contents) -> Optional[int]:
    reader = csv.reader(io.StringIO(strip_blank(file_contents)))
    lines_count = sum(1 for _ in enumerate(reader))

    if lines_count < self.k:
      return 0 - 1
    
    return (lines_count - self.k) - 1

  def is_leading_stripper(self) -> bool:
    return False

  @abstractmethod
  def is_trailing_stripper(self) -> bool:
    return True


class _RemoveBeforePatternStripper(Stripper):
  """ Currently not implemented!
  """

  def __init__(self, pattern: str, includes: bool):
    self.pattern = pattern
    self.includes = includes

  def is_leading_stripper(self) -> bool:
    return True

  @abstractmethod
  def is_trailing_stripper(self) -> bool:
    return False
    

class _RemoveAfterPatternStripper(Stripper):
  """ Currently not implemented!
  """

  def __init__(self, pattern: str, includes: bool):
    self.pattern = pattern
    self.includes = includes

  def is_leading_stripper(self) -> bool:
    return False

  @abstractmethod
  def is_trailing_stripper(self) -> bool:
    return True


class Transformer(object):
  
  def __init__(self, name: str, patterns: Optional[Dict[str, str]], rules: Optional[Dict[str, RuleDecl]]):
    Transformer.validate_rules(rules)
    assert(isinstance(name, str))
    assert(patterns is None or isinstance(patterns, dict))
    assert(rules is None or isinstance(rules, dict))
    self.name = name
    self.patterns = patterns
    self.rules = rules
  
  def __str__(self) -> str:
    patterns_desc: str = '\n'.join(['    {k} : {v}'.format(k=k, v=self.patterns[k]) for k in self.patterns])
    rules_desc: str = '\n'.join(['    {k} : {v}'.format(k=k, v=self.rules[k]) for k in self.rules])
    return """\
-
  patterns:
{patterns}
  rules:
{rules}
""".format(patterns=patterns_desc, rules=rules_desc)
  
  @staticmethod
  def make_transformers_with_serialization(serialization, tokenizer: Tokenizer) -> List['Transformer']:
    if not isinstance(serialization, list):
      return list()
    
    return [Transformer.make_with_serialization(c, tokenizer) for c in serialization]
  
  @staticmethod
  def make_with_serialization(serialization, tokenizer: Tokenizer) -> 'Transformer':
    if serialization is None:
      return Transformer('Unnamed Transformer', None, None)

    name = serialization.get('name', 'Unnamed Transformer')
    assert(isinstance(name, str), 'name is {} in {}'.format(name, serialization))

    patterns = serialization.get('patterns', dict())
    if patterns is None:
      patterns = dict()
    assert(isinstance(patterns, dict), 'patterns is {} in {}'.format(patterns, serialization))

    raw_rule = serialization.get('rules', dict())
    assert(isinstance(raw_rule, dict), 'rules is {} in {}'.format(raw_rule, serialization))

    rules: Dict[str, RuleDecl] = dict()

    for each_key in raw_rule:
      ast_context = ASTContext(tokenizer, raw_rule[each_key])
      rules[each_key] = ast_context.make_syntax()

    return Transformer(name, patterns, rules)
  
  @staticmethod
  def validate_rules(rules: Optional[Dict[str, str]]):
    if rules is None:
      return

    for each_rule_name in rules:
      if each_rule_name not in TRANSACTION_PROPERTY_KEYS:
        raise Exception('Unexpected rule name: {r}'.format(r=each_rule_name))

  def map_value(self, name: str, variables: Dict[str, str]) -> Optional[str]:
    assert(isinstance(name, str))
    assert(isinstance(variables, dict))
    syntax = self.get_rule_syntax(name)
    if syntax is None:
      return None
    return syntax.evaluate(variables)

  def get_rule_syntax(self, name: str) -> Optional[RuleDecl]:
    assert(isinstance(name, str))
    return self.rules.get(name)


class Importer:

  @staticmethod
  def make_importers(config) -> List['Importer']:
    if not isinstance(config, list):
      return list()

    return [Importer.make_importer(x) for x in config]

  @staticmethod
  def make_importer(config) -> 'Importer':
    assert(config is not None)
    
    name = config.get('name', None)
    encoding = config.get('encoding', None)
    probe = Probe.make_with_serialization(config.get('probe'))
    table_header = TableHeader.make_with_serialization(config.get('table_header'))
    strippers = Stripper.make_strippers_with_serialization(config.get('strippers'))
    variable_map = config.get('variables', dict())
    transformers = Transformer.make_transformers_with_serialization(config.get('transformers'), Tokenizer())

    return Importer(
      name, 
      encoding,
      probe, 
      table_header, 
      strippers, 
      variable_map, 
      transformers
    )
  
  def __init__(
    self, 
    name: Optional[str], 
    encoding: Optional[str],
    probe: Probe, 
    table_header: TableHeader, 
    strippers: List[Stripper], 
    variable_map: Dict[str, str], 
    transformers: List[Transformer]
  ):
    self.name = name if name is not None else make_default_impoter_name()
    self.probe = probe
    self.encoding = encoding
    self.table_header = table_header
    self.strippers = strippers
    self.variable_map = variable_map
    self.transformers = transformers
  
  def extend_with_extension(self, extension: 'ImporterExtension'):
    assert(isinstance(extension, ImporterExtension))
    assert(self.name == extension.name)
    if extension.probe is not None:
      print('Importer extension may not have probe.')
      print('Probe: {}'.format(extension.probe))
    if extension.table_header is not None:
      print('Importer extension may not have table header.')
      print('Table header: {}'.format(extension.table_header))
    self.strippers.extend(extension.strippers)
    self.variable_map.update(extension.variable_map)
    self.transformers.extend(extension.transformers)

  def normalize(self, file_contents) -> List[List[str]]:
    reader = csv.reader(io.StringIO(strip_blank(file_contents)))

    normalized_contents = list()

    stripped_leading_lines = self._get_stripped_leading_lines(file_contents)
    stripped_trailing_lines = self._get_stripped_trailing_lines(file_contents)

    line = next(reader, None)
    line_number = 0

    while line is not None:
      previous_line = line
      previous_line_number = line_number

      line = next(reader, None)
      line_number += 1

      if stripped_leading_lines is not None:
        if previous_line_number < stripped_leading_lines:
          continue
      if stripped_trailing_lines is not None:
        if previous_line_number > stripped_trailing_lines:
          continue
      
      normalized_contents.append(previous_line)

    return normalized_contents
  
  def _get_stripped_leading_lines(self, file_contents) -> Optional[int]:
    line_to_strip = None

    for each_stripper in self.strippers:
      if each_stripper.is_leading_stripper():
        line = each_stripper.evaluate_in_file_contents(file_contents)
        if line_to_strip is not None:
          line_to_strip = max(line, line_to_strip)
        else:
          line_to_strip = line
    
    return line_to_strip

  def _get_stripped_trailing_lines(self, file_contents) -> Optional[int]:
    line_to_strip = None

    for each_stripper in self.strippers:
      if each_stripper.is_trailing_stripper():
        line = each_stripper.evaluate_in_file_contents(file_contents)
        if line_to_strip is not None:
          line_to_strip = min(line, line_to_strip)
        else:
          line_to_strip = line
    
    return line_to_strip
  

class ImporterExtension(Importer):

  @staticmethod
  def make_importers_with_serialization(serialization) -> List['ImporterExtension']:
    assert(isinstance(serialization, list), "{}".format(serialization))
    return [ImporterExtension.make_with_serialization(c) for c in serialization]

  @staticmethod
  def make_with_serialization(serialization, extracted_name: Optional[str] = None) -> 'ImporterExtension':
    assert(serialization is not None)
    
    name = serialization.get('name')
    if name is None and extracted_name is not None:
      name = extracted_name
    assert(name is not None, 'Importer extension may have a name.')
    assert(isinstance(name, str))
    strippers = Stripper.make_strippers_with_serialization(serialization.get('strippers'))
    variable_map = serialization.get('variables', dict())
    transformers = Transformer.make_transformers_with_serialization(serialization.get('transformers'), Tokenizer())

    return ImporterExtension(
      name, 
      None, # Do not need to check encoding for extensions.
      None, 
      None, 
      strippers, 
      variable_map, 
      transformers
    )

  @staticmethod
  def make_named_importer_extensions_from_serialization(serialization) -> List['ImporterExtension']:
    assert(isinstance(serialization, dict))
    extensions = list()
    for key in serialization:
      if key.startswith('extends_'):
        name = key.removeprefix('extends_')
        if serialization[key] is not None:
          extension = ImporterExtension.make_with_serialization(serialization[key], extracted_name=name)
          extensions.append(extension)
    return extensions


class BPCML:

  @staticmethod
  def make_with_serialization_at_path(path: str) -> 'BPCML':
    with open(path, 'r') as config_file:
      serialization = yaml.safe_load(config_file)
      config = BPCML.make_with_serialization(serialization)
      config.cwd = os.path.dirname(path)
      config.path = path
      return config

  @staticmethod
  def make_with_serialization(serialization: Optional[Dict]) -> 'BPCML':
    if serialization is not None:
      developer = Developer.make_with_serialization(serialization.get('developer'))
      disabled_importers = serialization.get('disabled_importers', list())
      include_list = serialization.get('include', list())
      importers = Importer.make_importers(serialization.get('importers', list()))
      importer_extensions = ImporterExtension.make_importers_with_serialization(serialization.get('extensions', list()))
      named_impoter_extensions = ImporterExtension.make_named_importer_extensions_from_serialization(serialization)
      importer_extensions.extend(named_impoter_extensions)
    else:
      developer = Developer()
      disabled_importers = list()
      include_list = list()
      importers = list()
      importer_extensions = list()
    
    return BPCML(developer, disabled_importers, include_list, importers, importer_extensions)

  def __init__(
    self, 
    developer: Developer, 
    disabled_importers: List, 
    include_list: List, 
    importers: List[Importer], 
    importer_extensions: List[ImporterExtension]
  ):
    self.developer = developer
    self.disabled_importers = disabled_importers
    self.include_list = include_list
    self.importers = importers
    self.importer_extensions = importer_extensions
    self._is_resolved = False
  
  def resolve(self):
    self._resolve(self)
  
  def _resolve(self, root: 'BPCML'):
    # Resolves the config. Extends the config's contents with include lists 
    # and importer extensions.

    if self._is_resolved:
      return

    cwd = self.cwd

    if cwd is None:
      return
    
    for each_include in self.include_list:
      full_include_path = os.path.join(cwd, each_include)
      included_config = BPCML.make_with_serialization_at_path(full_include_path)
      if included_config is not None:
        self._extend_with_config(included_config, root)

    for each_importer_extension in self.importer_extensions:
      for each_importer in root.importers:
        if each_importer.name == each_importer_extension.name:
          each_importer.extend_with_extension(each_importer_extension)

    self._is_resolved = True

  def extend_with_config(self, config: 'BPCML'):
    self._extend_with_config(config, self)

  def _extend_with_config(self, config: 'BPCML', root_config: 'BPCML'):
    if config == self:
      return
    
    # Resolve the given config firstly. Thus we don't have to process configs
    # referred by its include-lists.
    config._resolve(root_config)

    # Only extends importers. Developer settings and disables importer list
    # hornors root config's setup.
    for each_importer in config.importers:
      existed_importer = next(filter(lambda i: i.name == each_importer.name, self.importers), None)
      if existed_importer is not None:
        logging.info('Importer with name \"{name}\" have already been there in config at path: {path}'.format(name=each_importer.name, path=self.path))
        continue
      self.importers.append(each_importer)

    for each_importer_extension in config.importer_extensions:
      for each_importer in self.importers:
        if each_importer.name == each_importer_extension.name:
          each_importer.extend_with_extension(each_importer_extension)
