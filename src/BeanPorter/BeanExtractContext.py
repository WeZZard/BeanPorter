#!/usr/bin/env python3

from typing import List, Dict, Optional, Tuple, Any

import re
import dateutil
import distutils.util
import logging

from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.number import D as to_decimal
from beancount.utils.date_utils import parse_date_liberally

from BeanPorter.bpcml.BPCML import Transformer, Importer
from BeanPorter.bpcml.BPCML import TRANSACTION_PROPERTY_KEYS, REQUIRED_TRANSACTION_PROPERTY_KEYS


class _VariableColumnMap(object):
  
  def __init__(self, variable_map: Dict[str, str], header: List[str]):
    variable_column_map: Dict[str, Tuple[re.Pattern, int]] = {}
    for variable_name in variable_map:
      column = variable_map[variable_name]
      column_index = header.index(column)
      if column_index is not None:
        if variable_name in variable_column_map.keys():
          logging.debug('Duplicate variable mapping: {n1} => {i1}, {n2} => {i2}. The latest is used.'.format(n1=variable_name, i1=variable_column_map[variable_name][1], n2=variable_name, i2=column_index))
        variable_column_map[variable_name] = tuple([re.compile(re.escape(variable_name)), column_index])
    self.variable_column_map = variable_column_map

  def get_column_for_term(self, searched_term: str) -> Optional[int]:
    for variable_name in self.variable_column_map:
      pattern_and_index = self.variable_column_map[variable_name]
      pattern: re.Pattern = pattern_and_index[0]
      index: int = pattern_and_index[1]
      if pattern.match(searched_term) is not None:
        return index
    
    return None

class BeanExtractRecord(object):

  def __init__(self, key: str, value: object, transformer: Transformer):
    assert(isinstance(key, str))
    assert(isinstance(transformer, Transformer))
    self.key = key
    self.value = value
    self.transformer = transformer

class BeanExtractContext(object):

  def __init__(self, flag: str, importer: Importer, header: List[str]):
    self.flag = flag
    self.importer = importer
    self.header = header
    self._dynamic_records: Dict[str, BeanExtractRecord] = dict()
    self._current_transformer: Optional[Transformer] = None
  
  def __setattr__(self, __name: str, __value: Any):
    if __name in TRANSACTION_PROPERTY_KEYS:
      self._set_dynamic_attr(__name, __value)
    else:
      super().__setattr__(__name, __value)

  def __getattr__(self, __name: str) -> Any:
    if __name in TRANSACTION_PROPERTY_KEYS:
      return self._get_dynamic_attr(__name)
    else:
      return super().__getattr__(__name)
  
  def _set_dynamic_attr(self, name: str, value: Any):
    assert(name in TRANSACTION_PROPERTY_KEYS)
    self._dynamic_records[name] = BeanExtractRecord(name, value, self._current_transformer)
  
  def _get_dynamic_attr(self, name: str) -> Any:
    assert(name in TRANSACTION_PROPERTY_KEYS)
    record = self._dynamic_records.get(name)
    if record is None:
      return None
    return record.value
  
  def _has_dynamic_attr(self, name: str) -> bool:
    assert(name in TRANSACTION_PROPERTY_KEYS)
    return name in self._dynamic_records
  
  def _get_latest_transformer_for_dynamic_attr(self, name: str) -> Optional[Transformer]:
    assert(name in TRANSACTION_PROPERTY_KEYS)
    record = self._dynamic_records.get(name)
    if record is None:
      return None
    return record.transformer

  def _push_transformer(self, transformer: Transformer):
    self._current_transformer = transformer
  
  def _pop_transformer(self) -> Transformer:
    assert(self._current_transformer is not None)
    retVal = self._current_transformer
    self._current_transformer = None
    return retVal
  
  def _cleanup(self):
    self._dynamic_records = dict()
  
  def _apply(self, transformer: Transformer, variables: Dict[str, str]):
    for each_key in TRANSACTION_PROPERTY_KEYS:
      self._apply_key_if_needed(each_key, transformer, variables)
  
  def _apply_key_if_needed(self, key: str, transformer: Transformer, variables: Dict[str, str]):
    value = transformer.map_value(key, variables)
    if value is not None:
      needs_set = True
      if self._has_dynamic_attr(key):
        previous_transformer = self._get_latest_transformer_for_dynamic_attr(key)
        needs_set = len(transformer.patterns) > len(previous_transformer.patterns)
      if needs_set:
        logging.debug('Apply {key} with {value}'.format(key=key, value=value))
        self._set_dynamic_attr(key, value)
  
  def _should_apply(self, transformer: Transformer, row: List[str], term_column_map: _VariableColumnMap) -> bool:
    """
    Check should apply the transformer to the row with terminology-column map.
    """
    
    all_pattenrs_matched = True

    for each_term in transformer.patterns:

      column_index = term_column_map.get_column_for_term(each_term)

      if column_index is None:
        logging.info('Cannot find column index for term: {t!r}.'.format(t=each_term))
        all_pattenrs_matched = False
          
      if not all_pattenrs_matched:
        return False

      column = row[column_index]

      raw_pattern = transformer.patterns[each_term]

      assert(raw_pattern is not None)

      #substitute terms in raw_pattern
      if raw_pattern.startswith('r\'') and raw_pattern.endswith('\''):
        # The raw pattern is decalred itself as a Python regex literal.
        # Thus compile it directory
        pattern = re.compile(raw_pattern[2:-1])
      else:
        # The raw pattern is not decalred itself as a Python regex literal.
        # Thus compile it after escaping.
        pattern = re.compile(re.escape(raw_pattern))

      if pattern.match(column) is not None:
        logging.debug('Pattern {p!r} is matched: {c!r}'.format(p=pattern.pattern, c=column))
      else:
        all_pattenrs_matched = False
        logging.debug('Pattern {p!r} is not matched: {c!r}'.format(p=pattern.pattern, c=column))
    
    return all_pattenrs_matched
  
  def _make_variables_with_row(self, row: List[str]) -> Dict[str, str]:
    variables = dict()

    for each_variable_name in self.importer.variable_map:
      each_column = self.importer.variable_map[each_variable_name]
      column_index: Optional[int] = None
      for (index, column_content) in enumerate(self.header):
        if column_content == each_column:
          column_index = index
          break
      assert(column_index != None)
      variables[each_variable_name] = row[column_index]
    
    return variables

  @staticmethod
  def _make_row_description(row: List[str]) -> str:
    return '| {} |'.format(' | '.join([column for column in row]))
  
  def _validate(self, row: List[str]):
    for each_required_key in REQUIRED_TRANSACTION_PROPERTY_KEYS:
      if each_required_key not in self._dynamic_records:
        logging.info('Required key {key} is missing for row: {row}'.format(key=each_required_key, row=BeanExtractContext._make_row_description(row)))
        return False
    
    is_transaction_complete = self.complete

    if is_transaction_complete is None:
      logging.fatal('Transaction completion info is not found for row: {}'.format(BeanExtractContext._make_row_description(row)))
      return False

    if self.debit_account is None or self.debit_amount is None:
      logging.info('Debit posting is missing for row: {}'.format(BeanExtractContext._make_row_description(row)))

    if self.credit_account is None or self.credit_amount is None:
      logging.info('Credit posting is missing for row: {}'.format(BeanExtractContext._make_row_description(row)))

    if not distutils.util.strtobool(is_transaction_complete):
      logging.info('Transaction is not complete for row: {}'.format(BeanExtractContext._make_row_description(row)))
      return False
    
    return True
  
  def evaluate(self, row: List[str], flags: str) -> Optional[data.Transaction]:

    # Clean up reults of previous evaluation.
    self._cleanup()

    variable_column_map = _VariableColumnMap(self.importer.variable_map, self.header)

    variables = self._make_variables_with_row(row)

    for each_transformer in self.importer.transformers:
      self._push_transformer(each_transformer)
      if self._should_apply(each_transformer, row, variable_column_map):
        self._apply(each_transformer, variables)
      self._pop_transformer()
    
    if not self._validate(row):
      return None

    date = parse_date_liberally(self.timestamp)
    time = dateutil.parser.parse(self.timestamp).time()

    meta = data.new_metadata('', 0)
    meta['date'] = date

    if self.time is not None:
      meta['time'] = time

    postings: List[data.Posting] = list()

    if self.debit_account and self.debit_amount:
      postings.append(
        data.Posting(
          self.debit_account, 
          Amount(to_decimal(self.debit_amount), self.debit_currency), 
          None,
          None,
          None,
          None))

    if self.credit_account and self.credit_amount:
      postings.append(
        data.Posting(
          self.credit_account, 
          Amount(to_decimal(self.credit_amount), self.credit_currency), 
          None,
          None,
          None,
          None))

    txn = data.Transaction(
      meta,
      date,
      flags,
      self.payee,
      self.transaction_name,
      set(), # tags
      set(), # links
      postings # postings
    )
    
    logging.debug('Transaction: {}'.format(txn))
    logging.debug('Record: {!r}'.format(BeanExtractContext._make_row_description(row)))

    return txn
