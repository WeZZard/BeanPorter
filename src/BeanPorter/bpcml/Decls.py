#!/usr/bin/env python3

from abc import abstractmethod
from typing import Dict, Optional

from BeanPorter.bpcml.Exprs import Expr

class Decl(object):

  def __init__(self):
    pass
  
  @abstractmethod
  def evaluate(self, variables: Dict[str, str]) -> str:
    pass

class RuleDecl(Decl):
  
  def __init__(self, expr: Optional[Expr] = None):
    self.expr = expr
    super().__init__()
  
  def __str__(self) -> str:
    return self.expr.__str__()
  
  def __repr__(self) -> str:
    return self.expr.__repr__()
  
  @abstractmethod
  def evaluate(self, variables: Dict[str, str]) -> str:
    if self.expr is None:
      return ""
    
    return self.expr.evaluate(variables)
  
  @staticmethod
  def make_empty() -> 'RuleDecl':
    return RuleDecl()
  
  @staticmethod
  def make(expr: Expr) -> 'RuleDecl':
    assert(expr is not None)
    return RuleDecl(expr)
