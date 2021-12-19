#!/usr/bin/env python3

from abc import abstractmethod
import dateutil
from typing import List, Optional

from beancount.utils.date_utils import parse_date_liberally

class BuiltinFunction(object):
  
  @abstractmethod
  def evaluate(self, args: List[str]) -> str:
    pass

  @staticmethod
  def make_with_name(name: str) -> Optional['BuiltinFunction']:
    if name == 'date':
      return BuiltinFunctionDate()
    if name == 'time':
      return BuiltinFunctionTime()
    if name == 'dy':
      return BuiltinFunctionDY()
    raise Exception("Cannot create builtin function from name: {}".format(name))


class BuiltinFunctionDate(BuiltinFunction):
  
  def evaluate(self, args: List[str]) -> str:
    return parse_date_liberally(args[0]).strftime('%Y-%m-%d')


class BuiltinFunctionTime(BuiltinFunction):
  
  def evaluate(self, args: List[str]) -> str:
    return dateutil.parser.parse(args[0]).time().strftime('%H:%M:%S')

class BuiltinFunctionDY(BuiltinFunction):
  """
  Drop prefixing CNY(¥) sign.
  """
  
  def evaluate(self, args: List[str]) -> str:
    if args[0].startswith('¥'):
      return args[0][1:]
    else:
      return args[0]
