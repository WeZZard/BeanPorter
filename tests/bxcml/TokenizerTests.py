#!/usr/bin/env python3

import unittest

from BeanPorter.bxcml.Tokenizer import Tokenizer
from BeanPorter.bxcml.Token import Token


class TokenizerTests(unittest.TestCase):

  def test_can_recognize_contiguous_alphabets(self):
    """
    Test that it can recognize abc
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("abc"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("abc")
    self.assertEqual(results, expected_results)

  def test_can_recognize_dash_separated_alphabets(self):
    """
    Test that it can recognize abc
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("abc-efg"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("abc-efg")
    self.assertEqual(results, expected_results)

  def test_can_recognize_dot_separated_alphabets(self):
    """
    Test that it can recognize abc
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("abc.efg"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("abc.efg")
    self.assertEqual(results, expected_results)

  def test_can_recognize_dot_separated_triple_numbers(self):
    """
    Test that it can recognize abc
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("123.456.789"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("123.456.789")
    self.assertEqual(results, expected_results)

  def test_can_recognize_spaced_alphabets(self):
    """
    Test that it can recognize abc efb
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("abc"), 
      Token.make_space(" "), 
      Token.make_string_literal("efg"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("abc efg")
    self.assertEqual(results, expected_results)

  def test_can_recognize_label_of_colon_separated_alphabets(self):
    """
    Test that it can recognize A:B:C
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal("A:B:C"),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("A:B:C")
    self.assertEqual(results, expected_results)

  def test_can_recognize_integer_numbers(self):
    """
    Test that it can recognize 123
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_numeric_literal('123'),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens('123')
    self.assertEqual(results, expected_results)

  def test_can_recognize_float_numbers(self):
    """
    Test that it can recognize 123.456
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_numeric_literal('123.456'),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("123.456")
    self.assertEqual(results, expected_results)

  def test_can_recognize_float_numbers_with_dot_end(self):
    """
    Test that it can recognize 123.0
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_numeric_literal('123.0'),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("123.0")
    self.assertEqual(results, expected_results)

  def test_can_recognize_float_numbers_with_dot_begin(self):
    """
    Test that it can recognize .456
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_numeric_literal('.456'),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens(".456")
    self.assertEqual(results, expected_results)

  def test_can_recognize_plus_operator(self):
    """
    Test that it can recognize +
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_plus(),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("+")
    self.assertEqual(results, expected_results)

  def test_can_recognize_minus_operator(self):
    """
    Test that it can recognize -
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_minus(),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("-")
    self.assertEqual(results, expected_results)

  def test_can_recognize_minus_variable(self):
    """
    Test that it can recognize -$variable
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_minus(),
      Token.make_dollar_sign(),
      Token.make_string_literal("variable"), 
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("-$variable")
    self.assertEqual(results, expected_results)

  def test_can_recognize_functioned_variable(self):
    """
    Test that it can recognize @func($variable)
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_at_sign(),
      Token.make_string_literal("func"),
      Token.make_left_paren(),
      Token.make_dollar_sign(),
      Token.make_string_literal("variable"),
      Token.make_right_paren(),
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("@func($variable)")
    self.assertEqual(results, expected_results)

  def test_can_recognize_comma(self):
    """
    Test that it can recognize ,
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_comma(), 
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens(",")
    self.assertEqual(results, expected_results)

  def test_can_recognize_comma_seperated_string_literal(self):
    """
    Test that it can recognize abc , efg
    """
    tokenizer = Tokenizer()
    expected_results = [
      Token.make_string_literal('abc'), 
      Token.make_space(" "), 
      Token.make_comma(), 
      Token.make_space(" "), 
      Token.make_string_literal('efg'), 
      Token.make_eof(),
    ]
    results = tokenizer.make_tokens("abc , efg")
    self.assertEqual(results, expected_results)

if __name__ == '__main__':
    unittest.main()
