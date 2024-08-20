from compiler.ast_node import ASTNode, ASTNodeVisitor
from compiler.symbol_table import SymbolTable, VarSymbol, FuncSymbol
from compiler.constants import ASTNodeType
from compiler.constants import VariableType


class SemanticError(Exception):
  """
  SemanticError
  =============
  The semantic error class is a class that is used to represent semantic errors
  that occur during semantic analysis. It is a subclass of the built-in
  Exception class.
  """


class SemanticAnalyzer(ASTNodeVisitor):
  """
  SemanticAnalyzer
  ================
  The SemanticAnalyzer class is a class that is used to perform semantic
  analysis on the abstract syntax tree. It checks for semantic errors such as
  undeclared variables and functions and type mismatches.
  """

  def __init__(self) -> None:
    self._current_scope = None

  def _error(self, message: str, node: ASTNode):
    raise SemanticError(
        f"{message}, line {node.token.line}, column {node.token.column}")

  def _generic_visit(self, node: ASTNode):
    if node.type in ASTNodeType:
      for child in node.children:
        self.visit(child)
    else:
      super()._generic_visit(node)

  def _visit_program(self, node: ASTNode):
    global_scope = SymbolTable("global", 1)
    self._current_scope = global_scope
    self._generic_visit(node)
    self._current_scope = self._current_scope.parent

  def _visit_id(self, node: ASTNode):
    var_name = node.token.value
    if self._current_scope.lookup(var_name) is None:
      self._error(f"Variable undefined '{var_name}'", node)

  def _visit_assign(self, node: ASTNode):
    return self._visit_id(node)

  def _visit_declaration(self, node: ASTNode):
    for child in node.children:
      var_name = child.token.value
      var_symbol = VarSymbol(var_name, VariableType(node.token.type.name))
      if self._current_scope.lookup(var_name, current_scope_only=True):
        self._error(f"Variable '{var_name}' already declared", child)
      self._current_scope.add(var_symbol)

  def _visit_func_decl(self, node: ASTNode):
    func_name = node.token.value
    if self._current_scope.lookup(func_name, current_scope_only=True):
      self._error(f"Function '{func_name}' already declared", node)
    func_scope = SymbolTable(
        func_name,
        self._current_scope.level + 1,
        self._current_scope,
    )
    self._current_scope = func_scope
    params, return_type, block = node.children
    func_symbol = FuncSymbol(
        func_name,
        VariableType(return_type.token.value),
        block_node=block,
        param_types=[],
    )
    for param in params.children:
      self._visit_declaration(param)
      func_symbol.param_types.extend(
          [VariableType(param.token.type.name)] * len(param.children))
    self.visit(block)
    self._current_scope = self._current_scope.parent
    self._current_scope.add(func_symbol)

  def _visit_call(self, node: ASTNode):
    func_name = node.token.value
    func_symbol = self._current_scope.lookup(func_name)
    if func_symbol is None:
      self._error(f"Function undefined '{func_name}'", node)
    if not isinstance(func_symbol, FuncSymbol):
      self._error(f"'{func_name}' is not a function", node)
    if len(func_symbol.param_types) != len(node.children):
      self._error(
          f"Function '{func_name}' expects {len(func_symbol.param_types)} "
          f"arguments, got {len(node.children)}",
          node,
      )
    self._generic_visit(node)

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #
