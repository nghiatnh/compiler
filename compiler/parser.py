from typing import List, Union
from enum import Enum


class NodeType(Enum):
  UNINIT = -1
  EMPTY = 0
  VAL = 1
  # Binary operators
  AND = 10
  OR = 11
  EQ = 12
  NE = 13
  LT = 14
  LE = 15
  GT = 16
  GE = 17
  ADD = 18
  SUB = 19
  MUL = 20
  DIV = 21
  MOD = 22
  # Unary operators
  NOT = 30
  NEG = 31
  # New scope
  DO = 40
  THEN = 41
  ELSE = 42
  # Variable declaration
  VAR = 50
  SET = 51
  SYM = 52
  # Control flow
  IF = 60
  LOOP = 61
  BREAK = 62
  CONTINUE = 63
  RETURN = 64
  # Functions
  DEF = 70
  CALL = 71
  SYSCALL = 72
  ARG = 73
  ARG_TYPE = 74


class Node:
  def __init__(
      self,
      type: NodeType = NodeType.UNINIT,
      value: Union[int, str] = None,
      children: List["Node"] = None
  ) -> None:
    self.type = type
    self.value = value
    self.children = children if children is not None else []


class Parser:
  def __init__(self) -> None:
    self.idx = 0
    self.query = ""

  @property
  def cur_char(self) -> str:
    return self.query[self.idx]

  @property
  def is_eof(self) -> bool:
    return self.idx >= len(self.query)

  def _move_next(self):
    self.idx += 1

  def _move_back(self):
    self.idx -= 1

  def _raise_error(self, msg: str):
    line = self.query.count("\n", 0, self.idx) + 1
    col = self.idx - self.query.rfind("\n", 0, self.idx)
    line_text = self.query.split("\n")[line - 1]
    return ValueError(
        f"Error at line {line}, column {col}:\n"
        f"{line_text}\n"
        f"Error: {msg}"
    )

  def parse(self, query: str) -> Node:
    self.idx = 0
    self.query = query
    node = self._parse_next_expr()
    self._skip_whitespace()
    if not self.is_eof:
      raise self._raise_error("traling garbage")
    return node

  def _parse_next_expr(self) -> Node:
    self._skip_whitespace()
    if self.cur_char == "(":
      self._move_next()
      node = Node()
      while True:
        self._skip_whitespace()
        if self.is_eof:
          self._raise_error("unbalanced parenthesis")
        if self.cur_char == ")":
          self._move_next()
          break
        if node.type == NodeType.UNINIT:
          expr = self._parse_next_expr()
          if len(expr.children) == 0:
            node.type = expr.type
            node.value = expr.value
          else:
            node.type = NodeType.EMPTY
            node.children.append(expr)
        else:
          node.children.append(self._parse_next_expr())
      return node
    elif self.cur_char == ")":
      raise self._raise_error("bad parenthesis")

    start = self.idx
    while (
        not self.is_eof and
        (not self.cur_char.isspace()) and
        self.cur_char not in "()"
    ):
      self._move_next()
    if start == self.idx:
      self._raise_error("empty expression")
    return _parse_atom(self.query[start:self.idx])

  def _skip_whitespace(self):
    while True:
      save = self.idx
      # skip whitespace
      while not self.is_eof and self.cur_char.isspace():
        self._move_next()
      # skip comment
      if not self.is_eof and self.cur_char == ";":
        self._move_next()
        if not self.is_eof and self.cur_char == ";":
          self._move_next()
          while not self.is_eof and self.cur_char != "\n":
            self._move_next()
        else:
          self._move_back()
      # if no progress, break
      if self.idx == save:
        break

  def parse_main(self, query: str) -> Node:
    return self.parse("(def (main int) () (do " + query + "))")


def _parse_atom(s: str) -> Node:
  import json
  try:
    val = json.loads(s)
    return Node(NodeType.VAL, val)
  except json.JSONDecodeError:
    if s == "and":
      return Node(NodeType.AND)
    if s == "or":
      return Node(NodeType.OR)
    if s == "eq":
      return Node(NodeType.EQ)
    if s == "ne":
      return Node(NodeType.NE)
    if s == "lt":
      return Node(NodeType.LT)
    if s == "le":
      return Node(NodeType.LE)
    if s == "gt":
      return Node(NodeType.GT)
    if s == "ge":
      return Node(NodeType.GE)
    if s == "+":
      return Node(NodeType.ADD)
    if s == "-":
      return Node(NodeType.SUB)
    if s == "*":
      return Node(NodeType.MUL)
    if s == "/":
      return Node(NodeType.DIV)
    if s == "%":
      return Node(NodeType.MOD)
    if s == "not":
      return Node(NodeType.NOT)
    if s == "neg":
      return Node(NodeType.NEG)
    if s == "do":
      return Node(NodeType.DO)
    if s == "then":
      return Node(NodeType.THEN)
    if s == "else":
      return Node(NodeType.ELSE)
    if s == "var":
      return Node(NodeType.VAR)
    if s == "set":
      return Node(NodeType.SET)
    if s == "if":
      return Node(NodeType.IF)
    if s == "loop":
      return Node(NodeType.LOOP)
    if s == "break":
      return Node(NodeType.BREAK)
    if s == "continue":
      return Node(NodeType.CONTINUE)
    if s == "return":
      return Node(NodeType.RETURN)
    if s == "def":
      return Node(NodeType.DEF)
    if s == "call":
      return Node(NodeType.CALL)
    if s == "syscall":
      return Node(NodeType.SYSCALL)
    return Node(NodeType.SYM, s)
