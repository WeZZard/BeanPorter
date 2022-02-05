#!/usr/bin/env python3

from abc import abstractmethod
from typing import Optional, Union, Dict, List

from BeanPorter.bpcml.Token import Token, TokenKind
from BeanPorter.bpcml.BuiltinFunctions import BuiltinFunction

def _make_indents(indent: int) -> str:
  return ''.join([ '  ' for _ in range(indent)])

class AnyExpr(object):

  def __init__(self):
    pass
  
  @abstractmethod
  def evaluate(self, variables: Dict[str, str]) -> str:
    pass

  def __repr__(self) -> str:
      return self._recursive_description(0)

  @abstractmethod
  def _recursive_description(self, indent: int) -> str:
    pass

class Expr(AnyExpr):

  def __init__(self, child: Optional['Expr'] = None):
    self.child = child

  def _recursive_description(self, indent: int) -> str:
    leading_spaces = _make_indents(indent)
    if self.child is None:
      return leading_spaces + '(Expr)'
    return leading_spaces + '(Expr \n' + self.child._recursive_description(indent + 1) + ')'

  def evaluate(self, variables: Dict[str, str]) -> str:
    if self.child is None:
      return ''
    return self.child.evaluate(variables)
  
  def _recursive_description(self, indent: int) -> str:
    if self.child is None:
      return 'Expr()'
    
    return """\
{indents}Expr(
{child})""".format(
      indents=_make_indents(indent),
      child=self.child._recursive_description(indent + 1)
    )
  
  @staticmethod
  def make_empty() -> 'Expr':
    return Expr()

  @staticmethod
  def make(child: 'Expr') -> 'Expr':
    return Expr(child)

class CompoundElement(object):
  
  @abstractmethod
  def evaluate(self, variables: Dict[str, str]) -> str:
    pass

class CompoundElementExpr(CompoundElement):

  def __init__(self, expr: Expr):
    assert(isinstance(expr, Expr))
    self.expr = expr

  def __str__(self) -> str:
    return self.expr.__str__()

  def _recursive_description(self, indent: int) -> str:
    return self.expr._recursive_description(indent)
  
  def evaluate(self, variables: Dict[str, str]) -> str:
    return self.expr.evaluate(variables)

class CompoundElementSpace(CompoundElement):

  def __init__(self, token: Token):
    assert(token.kind == TokenKind.Space)
    self.token = token

  def __str__(self) -> str:
    return self.token.contents

  def evaluate(self, variables: Dict[str, str]) -> str:
    return self.token.contents

class CompoundExpr(AnyExpr):
  
  def __init__(self, elements: List[CompoundElement] = {}):
    self.elements = elements
  
  def evaluate(self, variables: Dict[str, str]) -> str:
    return ''.join([e.evaluate(variables) for e in self.elements])

  def __str__(self) -> str:
    return ''.join([e.__str__() for e in self.elements])
  
  def _recursive_description(self, indent: int) -> str:
    if len(self.elements) == 0:
      return '{indents}CompoundExpr()'.format(indents=_make_indents(indent))
    
    elements_recursive_desc = ',\n'.join([e._recursive_description(indent + 1) for e in filter(lambda x: isinstance(x, CompoundElementExpr), self.elements)])

    return """\
{indents}CompoundExpr(
{elements_recursive_desc})""".format(
      indents=_make_indents(indent),
      elements_recursive_desc=elements_recursive_desc
    )

  @staticmethod
  def make_empty() -> 'CompoundExpr':
    return CompoundExpr()

  @staticmethod
  def make_unary(expr: Expr) -> 'CompoundExpr':
    return CompoundExpr({CompoundElementExpr(expr)})

  @staticmethod
  def make_binary(
    lhs: Expr, 
    space: Token, 
    rhs: 'CompoundExpr'
  ) -> 'CompoundExpr':
    elements: List[CompoundElement] = []
    elements.append(CompoundElementExpr(lhs))
    elements.append(CompoundElementSpace(space))
    elements.extend(rhs.elements)
    return CompoundExpr(elements)

class ValueExpr(AnyExpr):

  @staticmethod
  def make_paren(
    left_paren: Token, 
    child: Expr, 
    right_paren: Token
  ) -> 'ValueExpr':
    return ParenExpr(left_paren, child, right_paren)

  @staticmethod
  def make_unary(child: 'ValueExpr') -> 'ValueExpr':
    return child

class ParenExpr(ValueExpr):
  
  def __init__(self, left_paren: Token, child: Expr, right_paren: Token):
    self.left_paren = left_paren
    self.child = child
    self.right_paren = right_paren
    super.__init__(child)
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      return self.child.evaluate(variables)

  def __str__(self) -> str:
    return ''.join([e.__str__() for e in {self.left_paren, self.child, self.right_paren}])
  
  def _recursive_description(self, indent: int) -> str:
    return """\
{indents}ParenExpr(
{indents}  (
{child}
{indents}  ))""".format(
      indents=_make_indents(indent),
      child=self.child._recursive_description(indent + 1)
    )

class FuncArgListElement(object):
  pass

class FuncArg(FuncArgListElement):
  
  def __init__(self, value_expr: ValueExpr):
    assert(isinstance(value_expr, ValueExpr))
    self.value_expr = value_expr
  
  def evaluate(self, variables: Dict[str, str]) -> str:
    return self.value_expr.evaluate(variables)

  def __str__(self) -> str:
    return self.value_expr.__str__()
  
  def _recursive_description(self, indent: int) -> str:
    return '{}'.format(self.value_expr._recursive_description(indent))

class FuncArgSeparator(FuncArgListElement):
  
  def __init__(self, space1: Token, comma: Token, space2: Token):
    assert(isinstance(space1, Token))
    assert(isinstance(comma, Token))
    assert(isinstance(space2, Token))
    assert(space1.kind == TokenKind.Space)
    assert(comma.kind == TokenKind.Comma)
    assert(space2.kind == TokenKind.Space)
    self.space1 = space1
    self.comma = comma
    self.space2 = space2

  def __str__(self) -> str:
    return ''.join([t.contents for t in {self.space1, self.comma, self.space2}])

class FuncArgListExpr(AnyExpr):

  def __init__(self, elements: List[FuncArgListElement] = {}):
    for each_element in elements:
      assert(isinstance(each_element, FuncArgListElement))
    self.elements: List[FuncArgListElement] = elements
  
  def take_args(self, variables: Dict[str, str]) -> List[str]:
    
    results: List[str] = []

    for each_element in self.elements:
      if isinstance(each_element, FuncArg):
        each_element: FuncArg = each_element
        results.append(each_element.evaluate(variables))

    return results

  def __str__(self) -> str:
    return ''.join([e.__str__() for e in self.each_element])
  
  def _recursive_description(self, indent: int) -> str:
    if len(self.elements) == 0:
      return '{indents}FuncArgListExpr()'.format(indents=_make_indents(indent))
    
    elements_recursive_desc = ',\n'.join([e._recursive_description(indent + 1) for e in filter(lambda x: isinstance(x, FuncArg), self.elements)])

    return """\
{indents}FuncArgListExpr(
{elements_recursive_desc})""".format(
      indents=_make_indents(indent),
      elements_recursive_desc=elements_recursive_desc
    )
  
  @staticmethod
  def make_empty() -> 'FuncArgListExpr':
    return FuncArgListExpr()
  
  @staticmethod
  def make_unary(arg0: ValueExpr) -> 'FuncArgListExpr':
    return FuncArgListExpr({FuncArg(arg0)})
 
  @staticmethod
  def make_binary(
    arg0: ValueExpr,
    space1: Token,
    comma: Token,
    space2: Token,
    arg1: 'FuncArgListExpr'
  ) -> 'FuncArgListExpr':
    element_0 = FuncArg(arg0)
    element_1 = FuncArgSeparator(space1, comma, space2)
    elements: List[FuncArgListElement] = [element_0, element_1]
    elements.extend(arg1.elements)
    return FuncArgListExpr(elements)

class FuncCallExpr(ValueExpr):
  
  def __init__(
    self,
    at_sign: Token,
    func_name: Token,
    left_paren: Token,
    func_arg_list: FuncArgListExpr,
    right_paren: Token):
    self.at_sign = at_sign
    self.func_name = func_name
    self.left_paren = left_paren
    self.func_arg_list = func_arg_list
    self.right_paren = right_paren
    self.func = BuiltinFunction.make_with_name(func_name.contents)

  def evaluate(self, variables: Dict[str, str]) -> str:
      args = self.func_arg_list.take_args(variables)
      return self.func.evaluate(args)

  def __str__(self) -> str:
    elements = {self.at_sign, self.func_name, self.left_paren, self.func_arg_list, self.right_paren}
    return ''.join([e.__str__() for e in elements])
  
  def _recursive_description(self, indent: int) -> str:
    return """\
{indents}FuncCallExpr(
{indents}  @ {func_name}
{func_arg_list})""".format(
      indents=_make_indents(indent),
      func_name=self.func_name.contents,
      func_arg_list=self.func_arg_list._recursive_description(indent + 1)
    )
  
  @staticmethod
  def make(
      at_sign: Token,
      func_name: Token,
      left_paren: Token,
      func_arg_list: FuncArgListExpr,
      right_paren: Token) -> 'FuncCallExpr':
    return FuncCallExpr(at_sign, func_name, left_paren, func_arg_list, right_paren)

class StrLitExpr(ValueExpr):

  def __init__(self, token: Token):
    assert(token.kind == TokenKind.StringLiteral)
    self.token = token
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      return self.token.contents

  def __str__(self) -> str:
    return self.token.contents
  
  def _recursive_description(self, indent: int) -> str:
    return '{indents}StrLitExpr( "{string_literal}" )'.format(
      indents=_make_indents(indent), 
      string_literal=self.token.contents)
  
  @staticmethod
  def make(token: Token) -> 'StrLitExpr':
    return StrLitExpr(token)


class NumExpr(ValueExpr):

  def __init__(self, token: Token):
    assert(token.kind == TokenKind.NumericLiteral)
    self.token = token
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      return self.token.contents

  def __str__(self) -> str:
    return self.token.contents
  
  def _recursive_description(self, indent: int) -> str:
    return '{indents}NumExpr( {numeric_literal} )'.format(
      indents=_make_indents(indent), 
      numeric_literal=self.token.contents)
  
  @staticmethod
  def make(token: Token) -> 'NumExpr':
    return NumExpr(token)


class BoolExpr(ValueExpr):

  def __init__(self, token: Token):
    assert(token.kind == TokenKind.BoolLiteral)
    self.token = token
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      return '{}'.format(self.token.contents)

  def __str__(self) -> str:
    return self.token.contents
  
  def _recursive_description(self, indent: int) -> str:
    return '{indents}BoolExpr( {bool_literal} )'.format(
      indents=_make_indents(indent), 
      bool_literal=self.token.contents)
  
  @staticmethod
  def make(token: Token) -> 'BoolExpr':
    return BoolExpr(token)


class VarRefExpr(ValueExpr):

  def __init__(
    self, 
    leading_dollar: Token, 
    var_name: Token, 
    trailing_dollar: Optional[Token] = None
  ):
    self.leading_dollar = leading_dollar
    self.var_name = var_name
    self.trailing_dollar = trailing_dollar
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      return variables[self.var_name.contents]
  
  def __str__(self) -> str:
    return ''.join([t.contents for t in {self.leading_dollar, self.var_name, self.trailing_dollar}])
  
  def _recursive_description(self, indent: int) -> str:
    if self.trailing_dollar is None:
      return '{indents}VarRefExpr( ${var_ref_name} )'.format(
        indents=_make_indents(indent), 
        var_ref_name=self.var_name.contents)
    else:
      return '{indents}VarRefExpr( ${var_ref_name}$ )'.format(
        indents=_make_indents(indent), 
        var_ref_name=self.var_name.contents)
  
  @staticmethod
  def make_open(leading_dollar: Token, var_name: Token) -> 'VarRefExpr':
    return VarRefExpr(leading_dollar, var_name)

  @staticmethod
  def make_closed(
    leading_dollar: Token, 
    var_name: Token, 
    trailing_dollar: Token
  ) -> 'VarRefExpr':
    return VarRefExpr(leading_dollar, var_name, trailing_dollar)

class ArithmeticExpr(ValueExpr):

  def __init__(self, prefix_operator: Token, child: Union[NumExpr, VarRefExpr]):
    self.prefix_operator = prefix_operator
    self.child = child
  
  def evaluate(self, variables: Dict[str, str]) -> str:
      if self.prefix_operator.kind == TokenKind.Plus:
        return self.child.evaluate(variables)

      if self.prefix_operator.kind == TokenKind.Minus:
        return '-' + self.child.evaluate(variables)
      
      raise Exception('Unexpected token kind: {}'.format(self.prefix_operator.kind))

  def __str__(self) -> str:
    return self.prefix_operator.contents + self.child.contents
  
  def _recursive_description(self, indent: int) -> str:
    return """\
{indents}ArithmeticExpr(
{indents}  {prefix_operator}
{child})""".format(
      indents=_make_indents(indent),
      prefix_operator=self.prefix_operator.contents,
      child=self.child._recursive_description(indent + 1)
    )

  @staticmethod
  def make_prefix(operator: Token, child: Union[NumExpr, VarRefExpr]) -> 'ArithmeticExpr':
    return ArithmeticExpr(operator, child)