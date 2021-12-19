#!/usr/bin/env python3

import unittest

from ..Exprs import ArithmeticExpr, NumExpr, StrLitExpr, VarRefExpr
from ..Exprs import FuncArgListExpr, FuncCallExpr
from ..Token import Token


class ExprTests(unittest.TestCase):
  
  def test_num_expr(self):
    expr = NumExpr.make(Token.make_numeric_literal('100'))
    self.assertEqual(expr.__repr__(), 'NumExpr( 100 )')
  
  def test_str_expr(self):
    expr = StrLitExpr.make(Token.make_string_literal('ABC:EFG:HIJ'))
    self.assertEqual(expr.__repr__(), 'StrLitExpr( "ABC:EFG:HIJ" )')
  
  def test_var_ref_expr_open(self):
    expr = VarRefExpr.make_open(Token.make_dollar_sign(), Token.make_string_literal('abc'))
    self.assertEqual(expr.__repr__(), 'VarRefExpr( $abc )')
  
  def test_var_ref_expr_closed(self):
    expr = VarRefExpr.make_closed(Token.make_dollar_sign(), Token.make_string_literal('abc'), Token.make_dollar_sign())
    self.assertEqual(expr.__repr__(), 'VarRefExpr( $abc$ )')
  
  def test_arithmetic_expr(self):
    num_expr = NumExpr.make(Token.make_numeric_literal('100'))
    arith_expr = ArithmeticExpr.make_prefix(Token.make_plus(), num_expr)
    self.assertEqual(arith_expr.__repr__(), """\
ArithmeticExpr(
  +
  NumExpr( 100 ))""")

  def test_func_arg_list_expr_empty(self):
    func_arg_list_expr = FuncArgListExpr.make_empty()
    self.assertEqual(func_arg_list_expr.__repr__(), 'FuncArgListExpr()')

  def test_func_arg_list_expr_unary(self):
    num_expr = NumExpr.make(Token.make_numeric_literal('100'))
    func_arg_list_expr = FuncArgListExpr.make_unary(num_expr)
    self.assertEqual(func_arg_list_expr.__repr__(), """\
FuncArgListExpr(
  NumExpr( 100 ))""")

  def test_func_arg_list_expr_binary(self):
    num_expr = NumExpr.make(Token.make_numeric_literal('100'))
    func_arg_list_expr1 = FuncArgListExpr.make_unary(num_expr)
    func_arg_list_expr2 = FuncArgListExpr.make_binary(
      num_expr, 
      Token.make_space(" "), 
      Token.make_comma(), 
      Token.make_space(" "), 
      func_arg_list_expr1)
    self.assertEqual(func_arg_list_expr2.__repr__(), """\
FuncArgListExpr(
  NumExpr( 100 ),
  NumExpr( 100 ))""")

  def test_func_call_empty_args(self):
    func_arg_list_expr = FuncArgListExpr.make_empty()
    func_call_expr = FuncCallExpr.make(Token.make_dollar_sign(), Token.make_string_literal("date"), Token.make_left_paren(), func_arg_list_expr, Token.make_right_paren())
    self.assertEqual(func_call_expr.__repr__(), """\
FuncCallExpr(
  @ date
  FuncArgListExpr())""")

  def test_func_call_unary_arg(self):
    num_expr = NumExpr.make(Token.make_numeric_literal('100'))
    func_arg_list_expr = FuncArgListExpr.make_unary(num_expr)
    func_call_expr = FuncCallExpr.make(Token.make_dollar_sign(), Token.make_string_literal("date"), Token.make_left_paren(), func_arg_list_expr, Token.make_right_paren())
    self.assertEqual(func_call_expr.__repr__(), """\
FuncCallExpr(
  @ date
  FuncArgListExpr(
    NumExpr( 100 )))""")

  def test_func_call_binary_arg(self):
    num_expr = NumExpr.make(Token.make_numeric_literal('100'))
    func_arg_list_expr1 = FuncArgListExpr.make_unary(num_expr)
    func_arg_list_expr2 = FuncArgListExpr.make_binary(
      num_expr, 
      Token.make_space(" "), 
      Token.make_comma(), 
      Token.make_space(" "), 
      func_arg_list_expr1)
    func_call_expr = FuncCallExpr.make(Token.make_dollar_sign(), Token.make_string_literal("date"), Token.make_left_paren(), func_arg_list_expr2, Token.make_right_paren())
    self.assertEqual(func_call_expr.__repr__(), """\
FuncCallExpr(
  @ date
  FuncArgListExpr(
    NumExpr( 100 ),
    NumExpr( 100 )))""")
