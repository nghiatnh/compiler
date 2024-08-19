class Symbol:
  """
  Symbol
  ======
  A class to represent a symbol in the symbol table.
  """

  def __init__(self, name: str, symbol_type: str):
    self.name = name
    self.type = symbol_type


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

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def add(self, symbol: Symbol):
    """
    Add a symbol to the symbol table.
    """
    self._symbols[symbol.name] = symbol

  def lookup(self, name: str, current_scope_only: bool = False) -> Symbol:
    """
    Lookup a symbol in the symbol table. If the symbol is not found in the
    current symbol table, lookup in the parent symbol table if it exists.
    """
    symbol = self._symbols.get(name, None)
    if symbol is not None:
      return symbol

    if current_scope_only:
      return None

    if self.parent is not None:
      return self.parent.lookup(name)

    return None
