from typing import List, Tuple
from dataclasses import dataclass

from compiler.ast_node import ASTNode
from compiler.byte_code import ByteCode
from compiler.constants import ReturnType


@dataclass
class ReturnData:
  """
  ReturnData
  ==========
  A class to represent the return data of a function.
  """
  rtype: ReturnType = ReturnType.VOID
  index: int = -1


class Symbol:
  """
  Symbol
  ======
  A class to represent a symbol in the symbol table.
  """

  def __init__(self, name: str, data: ReturnData = None):
    self.name = name
    self.data = data or ReturnData()

  @property
  def type(self) -> ReturnType:
    return self.data.rtype

  @property
  def index(self) -> int:
    return self.data.index

  @index.setter
  def index(self, value: int):
    self.data.index = value

  def __repr__(self) -> str:
    return f"<Symbol\t{self.name}>"

  def __str__(self) -> str:
    return self.__repr__()


class VarSymbol(Symbol):
  """
  VarSymbol
  =========
  A class to represent a variable symbol in the symbol table.
  """

  def __init__(self, name: str, var_type: ReturnType):
    super().__init__(name, ReturnData(rtype=var_type))

  def __repr__(self) -> str:
    return f"<VarSymbol\t{self.name}:\t{self.type.name}>"


class FuncSymbol(Symbol):
  """
  ProcDeclSymbol
  ==============
  A class to represent a procedure declaration symbol in the symbol table.
  """

  def __init__(
      self,
      name: str,
      return_type: ReturnType,
      block_node: ASTNode = None,
      param_types: List[ReturnType] = None
  ):
    super().__init__(name, ReturnData(rtype=return_type))
    self.param_types: List[ReturnType] = param_types or []
    self.block_node: ASTNode = block_node

  def __repr__(self) -> str:
    param_types = ", ".join([x.name for x in self.param_types])
    return f"<FuncSymbol\t{self.name}\t({param_types}):\t{self.type.name}>"


class SymbolTable:
  """
  SymbolTable
  ===========
  A class to represent a symbol table.
  """

  def __init__(self, name: str, level: int, parent: "SymbolTable" = None):
    self._symbols = {}
    self.name = name
    self.level = level
    self.parent = parent
    self.children: List[SymbolTable] = []
    self.code: List[ByteCode] = []
    self.stack = 0
    self.labels = []

  def __str__(self) -> str:
    h1 = "SCOPE INFO"
    lines = ["\n", h1, "=" * len(h1)]
    for header_name, header_value in (
        ("Scope name", self.name),
        ("Scope level", self.level),
        ("Parent scope", self.parent.name if self.parent is not None else None),
        ("Children scopes", ", ".join([x.name for x in self.children])),
        ("Stack size", self.stack),
        ("Labels", ", ".join(map(str, self.labels))),
    ):
      lines.append(f"{header_name:<15s}: {header_value}")
    h2 = "Scope contents"
    lines.extend([h2, "-" * len(h2)])
    lines.extend(
        [f"{key}: {value!r}" for key, value in self._symbols.items()]
    )
    lines.append("\n")
    s = "\n".join(lines)
    return s

  def __repr__(self) -> str:
    return str(self)

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def add(self, symbol: Symbol):
    """
    Add a symbol to the symbol table.
    """
    symbol.index = self.new_var()
    self._symbols[symbol.name.upper()] = symbol

  def lookup(
      self, name: str, current_scope_only: bool = False
  ) -> Tuple[int, Symbol]:
    """
    Lookup a symbol in the symbol table. If the symbol is not found in the
    current symbol table, lookup in the parent symbol table if it exists.
    """
    symbol = self._symbols.get(name.upper(), None)
    if symbol is not None:
      return self.level, symbol

    if current_scope_only:
      return -1, None

    if self.parent is not None:
      return self.parent.lookup(name.upper())

    return -1, None

  def new_var(self) -> int:
    """
    Allocate a new variable in the stack.
    """
    self.stack += 1
    return self.stack - 1

  def new_label(self) -> int:
    """
    Allocate a new label.
    """
    self.labels.append(-1)
    return len(self.labels) - 1

  def set_label(self, index: int, value: int):
    """
    Set the value of a label.
    """
    self.labels[index] = value
