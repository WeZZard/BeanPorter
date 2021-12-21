#!/usr/bin/env python3

import enum

class TokenKind(enum.IntEnum):
  StringLiteral = 0
  NumericLiteral = 1
  BoolLiteral = 2
  Space = 3
  Plus = 4
  Minus = 5
  DolarSign = 6
  AtSign = 7
  Comma = 8
  LeftParen = 9
  RightParen = 10
  Eof = 11
  
  def __repr__(self) -> str:
    if self == TokenKind.StringLiteral:
      return "StringLiteral"
    if self == TokenKind.NumericLiteral:
      return "NumericLiteral"
    if self == TokenKind.BoolLiteral:
      return "BoolLiteral"
    if self == TokenKind.Space:
      return "Space"
    if self == TokenKind.Plus:
      return "Plus"
    if self == TokenKind.Minus:
      return "Minus"
    if self == TokenKind.DolarSign:
      return "Dolar Sign"
    if self == TokenKind.AtSign:
      return "At Sign"
    if self == TokenKind.Comma:
      return "Comma"
    if self == TokenKind.LeftParen:
      return "Left Parenthesis"
    if self == TokenKind.RightParen:
      return "Right Parenthesis"
    if self == TokenKind.Eof:
      return "Epsilon"
    raise Exception("Unexpected identifier with value: {v}".format(v=self))


class Token(object):

  def __init__(self, kind: TokenKind, contents: str):
    assert(isinstance(kind, TokenKind))
    assert(isinstance(contents, str), 'contents is type: {}'.format(type(contents)))
    self.kind = kind
    self.contents = contents

  def __eq__(self, __o: object) -> bool:
    if type(__o) is not Token:
      return False
    return __o.kind == self.kind and __o.contents == self.contents

  def __repr__(self) -> str:
    return '<Token: {addr}; Kind = {kind!r}, Contents = {contents!r}>'.format(
      addr=hex(id(self)), 
      kind=self.kind, 
      contents=self.contents
    )

  @staticmethod
  def make_string_literal(string: str) -> 'Token':
    return Token(TokenKind.StringLiteral, string)

  @staticmethod
  def make_numeric_literal(string: str) -> 'Token':
    return Token(TokenKind.NumericLiteral, string)

  @staticmethod
  def make_bool_literal(flag: bool) -> 'Token':
    return Token(TokenKind.BoolLiteral, flag)

  @staticmethod
  def make_space(string: str) -> 'Token':
    return Token(TokenKind.Space, string)

  @staticmethod
  def make_plus() -> 'Token':
    return Token(TokenKind.Plus, '+')

  @staticmethod
  def make_minus() -> 'Token':
    return Token(TokenKind.Minus, '-')

  @staticmethod
  def make_dollar_sign() -> 'Token':
    return Token(TokenKind.DolarSign, '$')

  @staticmethod
  def make_at_sign() -> 'Token':
    return Token(TokenKind.AtSign, '@')

  @staticmethod
  def make_comma() -> 'Token':
    return Token(TokenKind.Comma, ',')

  @staticmethod
  def make_left_paren() -> 'Token':
    return Token(TokenKind.LeftParen, '(')

  @staticmethod
  def make_right_paren() -> 'Token':
    return Token(TokenKind.RightParen, ')')

  @staticmethod
  def make_eof() -> 'Token':
    return Token(TokenKind.Eof, '')
