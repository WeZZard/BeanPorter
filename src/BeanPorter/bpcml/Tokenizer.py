#!/usr/bin/env python3

from typing import Union, List, Optional

import re

from BeanPorter.bpcml.Token import Token


class Tokenizer(object):

  _TOKEN_PATTERNS: Optional[re.Pattern] = None

  @staticmethod
  def _get_token_patterns() -> re.Pattern:
    if Tokenizer._TOKEN_PATTERNS is not None:
      return Tokenizer._TOKEN_PATTERNS

    space           = "(?P<space>\s+)"
    plus            = "(?P<plus>\+)"
    minus           = "(?P<minus>\-)"
    dollar_sign     = "(?P<dollar_sign>\$)"
    at_sign         = "(?P<at_sign>@)"
    comma           = "(?P<comma>,)"
    left_paren      = "(?P<left_paren>\()"
    right_paren     = "(?P<right_paren>\))"
    # multi-dot separated numbers string literal
    number_like     = "(?P<string_literal_number_like>[+-]?(\.\d+(\.\d+))|(\d+\.\d+(\.\d+)+)|(\d+\.\.+))"
    numeric_literal = "(?P<numeric_literal>[+-]?(\.\d+)|(\d+\.\d+)|(\d+\.?))"
    # if not all above, then be literal.
    string_literal  = "(?P<string_literal>[^\s()]+)"

    # Priorities descends along the order of appending
    patterns: List[str] = list()
    patterns.append(space)
    patterns.append(plus)
    patterns.append(minus)
    patterns.append(dollar_sign)
    patterns.append(at_sign)
    patterns.append(comma)
    patterns.append(left_paren)
    patterns.append(right_paren)
    patterns.append(number_like)
    patterns.append(numeric_literal)
    patterns.append(string_literal)

    token_patterns = re.compile("|".join(patterns))

    Tokenizer._TOKEN_PATTERNS = token_patterns

    return token_patterns

  def make_tokens(self, contents: Union[str, bool]) -> List[Token]:
    if isinstance(contents, bool):
      return [Token.make_bool_literal(contents), Token.make_eof()]

    stripped_string = contents.strip()
    token_patterns = Tokenizer._get_token_patterns()

    tokens: List[Token] = list()

    for each_match in re.finditer(token_patterns, stripped_string):
      if each_match.lastgroup == 'string_literal_number_like':
        tokens.append(Token.make_string_literal(each_match.groups()[each_match.lastindex-1]))
      if each_match.lastgroup == 'string_literal':
        tokens.append(Token.make_string_literal(each_match.groups()[each_match.lastindex-1]))
      if each_match.lastgroup == 'numeric_literal':
        tokens.append(Token.make_numeric_literal(each_match.groups()[each_match.lastindex-1]))
      if each_match.lastgroup == 'space':
        tokens.append(Token.make_space(each_match.groups()[each_match.lastindex-1]))
      if each_match.lastgroup == 'plus':
        tokens.append(Token.make_plus())
      if each_match.lastgroup == 'minus':
        tokens.append(Token.make_minus())
      if each_match.lastgroup == 'dollar_sign':
        tokens.append(Token.make_dollar_sign())
      if each_match.lastgroup == 'at_sign':
        tokens.append(Token.make_at_sign())
      if each_match.lastgroup == 'comma':
        tokens.append(Token.make_comma())
      if each_match.lastgroup == 'left_paren':
        tokens.append(Token.make_left_paren())
      if each_match.lastgroup == 'right_paren':
        tokens.append(Token.make_right_paren())
      
    tokens.append(Token.make_eof())
    
    return tokens
