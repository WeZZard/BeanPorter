#!/usr/bin/env python3

from typing import List, Optional

import sys
import logging

from BeanPorter.bpcml.Tokenizer import Tokenizer
from BeanPorter.bpcml.Token import Token, TokenKind
from BeanPorter.bpcml.Decls import RuleDecl
from BeanPorter.bpcml.Exprs import ArithmeticExpr, BoolExpr, Expr, CompoundExpr, FuncArgListExpr, NumExpr, StrLitExpr
from BeanPorter.bpcml.Exprs import ValueExpr, VarRefExpr, FuncCallExpr

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

"""

BNF
===

RuleDecl -> CompoundExpr eof
          | eof

CompoundExpr -> Expr [space] CompoundExpr
              | epsilon

Expr -> ValueExpr
      | epsilon

ValueExpr -> ParenExpr
           | StrLitExpr
           | ArithmeticExpr
           | NumExpr
           | BoolExpr
           | VarRefExpr
           | FuncCallExpr

ParenExpr -> ( ValueExpr )

ArithmeticExpr -> + NumExpr
                | - NumExpr
                | + VarRefExpr
                | - VarRefExpr

NumExpr -> numeric_literal

FuncCallExpr -> @ string_literal ( FuncArgListExpr )

FuncArgListExpr -> ValueExpr
                 | ValueExpr [space] , [space] FuncArgListExpr
                 | epsilon

StrLitExpr -> string_literal

VarRefExpr -> $ identifier
            | $ identifier $

BoolExpr -> boolean_literal

"""


class ASTContext(object):

  def __init__(self, tokenizer: Tokenizer, string: str):
    self.tokenizer = tokenizer
    self.contents = string
    self._tokens: Optional[Token] = None
    self._index = 0
    self._error: Optional[str] = None

  def _get_tokens(self) -> List[Token]:
    if self._tokens is not None:
      return self._tokens
    
    tokens = self.tokenizer.make_tokens(self.contents)

    if len(tokens) < 1:
      raise Exception("No tokens can be created from string: {s}".format(s=self.contents))

    self._tokens = tokens
    return tokens

  def _peek(self) -> Token:
    return self._get_tokens()[self._index]

  def _consume(self) -> Token:
    self._index += 1
    return self._get_tokens()[self._index]

  def make_syntax(self) -> Optional[RuleDecl]:
    top_level_decl = self._top_level_decl()
    if top_level_decl is None:
      logging.fatal("Error happened while parsing \"{s}\": {e}".format(s=self.contents, e=self._error))
    return top_level_decl

  def _top_level_decl(self) -> Optional[RuleDecl]:
    token = self._peek()

    if token.kind == TokenKind.Eof:
      self._consume()
      return RuleDecl.make_empty()

    compound_expr = self._compound_expr()

    if compound_expr is None:
      self._error = "Cannot parse {}".format(self.contents)
      return None

    return RuleDecl.make(compound_expr)

  def _compound_expr(self) -> Optional[CompoundExpr]:
    token = self._peek()
    
    if token.kind == TokenKind.Eof:
      self._consume()
      return CompoundExpr.make_empty()

    expr = self._expr()

    if expr is None:
      self._error = "Cannot parse {}".format(self.contents)
      return None

    token = self._peek()

    space: Optional[Token] = None

    if token.kind == TokenKind.Space:
      self._consume()
      space = token
    else:
      return CompoundExpr.make_unary(expr)

    compound_expr = self._compound_expr()

    if compound_expr is None:
      self._error = "Cannot parse {}".format(self.contents)
      return None

    return CompoundExpr.make_binary(expr, space, compound_expr)

  def _expr(self) -> Expr:
    token = self._peek()

    if token.kind == TokenKind.Eof:
      self._consume()
      return Expr.make_empty()

    value_expr = self._value_expr()

    if value_expr is None:
      self._error = "Cannot parse {}".format(self.contents)
      return None

    return Expr.make(value_expr)
  
  def _value_expr(self) -> ValueExpr:
    token = self._peek()

    if token.kind == TokenKind.LeftParen:
      left_paren = token
      self._consume()
      
      child = self._value_expr()
      if child is None:
        self._error = "Cannot parse {}".format(self.contents)
        return None
      
      token = self._peek()

      if token.kind == TokenKind.RightParen:
        right_paren = token
        self._consume()

        return ValueExpr.make_paren(left_paren, child, right_paren)
      else:
        self._error = "Expect paired right parenthesis."
        return None
    
    child = self._arithmetic_expr()
    if child is not None:
      return ValueExpr.make_unary(child)
    
    child = self._num_expr()
    if child is not None:
      return ValueExpr.make_unary(child)

    child = self._func_call_expr()
    if child is not None:
      return ValueExpr.make_unary(child)

    child = self._str_lit_expr()
    if child is not None:
      return ValueExpr.make_unary(child)

    child = self._bool_expr()
    if child is not None:
      return ValueExpr.make_unary(child)

    child = self._var_ref_expr()
    if child is not None:
      return ValueExpr.make_unary(child)
    
    self._error = "Cannot parse {}".format(self.contents)
    return None
  
  def _arithmetic_expr(self) -> ArithmeticExpr:
    token = self._peek()

    if token.kind != TokenKind.Plus and token.kind != TokenKind.Minus:
      self._error = "Expecting + or -"
      return None
    
    operator = token
    self._consume()
    
    num_expr = self._num_expr()

    if num_expr is not None:
      return ArithmeticExpr.make_prefix(operator, num_expr)
    
    var_ref_expr = self._value_expr()
    if var_ref_expr is not None:
      return ArithmeticExpr.make_prefix(operator, var_ref_expr)

    self._error = "Cannot parse {}".format(self.contents)
    return None

  def _num_expr(self) -> NumExpr:
    token = self._peek()

    if token.kind != TokenKind.NumericLiteral:
      self._error = "Expecting numeric literal"
      return None
    
    self._consume()
    return NumExpr.make(token)
  
  def _func_call_expr(self) -> FuncCallExpr:
    token = self._peek()

    if token.kind != TokenKind.AtSign:
      self._error = "expecting @"
      return None
    
    at_sign = token
    token = self._consume()
    
    if token.kind != TokenKind.StringLiteral:
      self._error = "Expecting function name"
      return None
    
    func_name = token
    token = self._consume()

    if token.kind != TokenKind.LeftParen:
      self._error = "Expecting ("
      return None
    
    left_paren = token
    token = self._consume()

    func_arg_list_expr = self._func_arg_list_expr()

    if func_arg_list_expr is None:
      self._error = "Cannot parse {}".format(self.contents)
      return None
    
    token = self._peek()
    
    if token.kind != TokenKind.RightParen:
      self._error = "Expecting )"
      return None
    
    right_paren = token
    self._consume()

    return FuncCallExpr.make(
      at_sign, 
      func_name, 
      left_paren, 
      func_arg_list_expr, 
      right_paren
    )
  
  def _func_arg_list_expr(self) -> FuncArgListExpr:
    value_expr = self._value_expr()

    if value_expr is None:
      return FuncArgListExpr.make_empty()
    
    token = self._peek()

    if token.kind != TokenKind.Space:
      return FuncArgListExpr.make_unary(value_expr)
    
    space_1 = token
    token = self._consume()

    if token.kind != TokenKind.Comma:
      self._error = "Expecting ,"
      return None
    
    comma = token
    token = self._consume()

    if token.kind != TokenKind.Space:
      self._error = "Expecting space"
      return None
    
    space_2 = token
    token = self._consume()

    func_arg_list_expr = self._func_arg_list_expr()

    return FuncArgListExpr.make_binary(
      value_expr, 
      space_1, 
      comma, 
      space_2, 
      func_arg_list_expr
    )
  
  def _str_lit_expr(self) -> StrLitExpr:
    token = self._peek()

    if token.kind != TokenKind.StringLiteral:
      self._error = "Expecting string literal"
      return None
    
    self._consume()
    return StrLitExpr.make(token)

  def _bool_expr(self) -> BoolExpr:
    token = self._peek()

    if token.kind != TokenKind.BoolLiteral:
      self._error = "Expecting bool literal"
      return None
    
    self._consume()
    return BoolExpr.make(token)
  
  def _var_ref_expr(self) -> VarRefExpr:
    token = self._peek()

    if token.kind != TokenKind.DolarSign:
      self._error = "Expecting $"
      return None
    
    dollar_sign = token
    token = self._consume()

    if token.kind != TokenKind.StringLiteral:
      self._error = "Expecting string literal"
      return None

    var_name = token
    token = self._consume()

    if token.kind == TokenKind.DolarSign:
      closed_dollar_sign = token
      self._consume()
      return VarRefExpr.make_closed(dollar_sign, var_name, closed_dollar_sign)
    
    return VarRefExpr.make_open(dollar_sign, var_name)
