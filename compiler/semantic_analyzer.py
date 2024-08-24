from compiler.ast_node import ASTNode, ASTNodeVisitor
from compiler.symbol_table import SymbolTable, VarSymbol, FuncSymbol
from compiler.constants import ASTNodeType
from compiler.constants import VariableType
from compiler.constants import TokenType


class SemanticError(Exception):
  """
  SemanticError
  =============
  The semantic error class is a class that is used to represent semantic errors
  that occur during semantic analysis. It is a subclass of the built-in
  Exception class.
  """


class Function:
  """
  Function
  ========
  """

  def __init__(self, func: FuncSymbol, parent: "Function" = None) -> None:
    self._func = func
    self._parent = parent

  @property
  def func(self) -> FuncSymbol:
    return self._func

  @property
  def parent(self) -> "Function":
    return self._parent


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
    self._current_func = None

  def _error(self, message: str, node: ASTNode):
    raise SemanticError(
        f"{message}, line {node.token.line}, column {node.token.column}")

  def _generic_visit(self, node: ASTNode) -> ASTNode:
    if node.type in ASTNodeType:
      for child in node.children:
        self.visit(child)
      return VariableType.VOID
    else:
      super()._generic_visit(node)

  def _visit_program(self, node: ASTNode) -> VariableType:
    global_scope = SymbolTable("global", 1)
    self._current_scope = global_scope
    self._generic_visit(node)
    self._current_scope = self._current_scope.parent
    return VariableType.VOID

  def _visit_binary_op(self, node: ASTNode) -> VariableType:
    left_type = self.visit(node.children[0])
    right_type = self.visit(node.children[1])
    if left_type != right_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == VariableType.VOID:
      self._error("Invalid type VOID", node)
    if node.token.type in (TokenType.AND, TokenType.OR):
      if left_type != VariableType.BOOLEAN:
        self._error(f"Invalid type {left_type.name}", node)
      return VariableType.BOOLEAN
    if node.token.type in (
        TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.LE,
        TokenType.GT, TokenType.GE
    ):
      return VariableType.BOOLEAN
    return left_type

  def _visit_unary_op(self, node: ASTNode) -> VariableType:
    return_type = self.visit(node.children[0])
    if node.token.type == TokenType.NOT:
      if return_type != VariableType.BOOLEAN:
        self._error(f"Invalid type {return_type.name}", node)
      return VariableType.BOOLEAN
    if return_type == VariableType.VOID:
      self._error("Invalid type VOID", node)
    return return_type

  def _visit_block(self, node: ASTNode) -> VariableType:
    var_decl, *func_decls, statements = node.children
    self.visit(var_decl)
    for func_decl in func_decls:
      self.visit(func_decl)
    return self._visit_statements(statements)

  def _visit_statements(self, node: ASTNode) -> VariableType:
    for child in node.children:
      if child.type == ASTNodeType.RETURN:
        return self.visit(child)
      self.visit(child)
    return VariableType.VOID

  def _visit_id(self, node: ASTNode) -> VariableType:
    var_name = node.token.value
    var_symbol = self._current_scope.lookup(var_name)
    if var_symbol is None:
      self._error(f"Variable undefined '{var_name}'", node)
    if not isinstance(var_symbol, VarSymbol):
      self._error(f"'{var_name}' is not a variable", node)
    return var_symbol.var_type

  def _visit_value(self, node: ASTNode) -> VariableType:
    if isinstance(node.token.value, bool):
      return VariableType.BOOLEAN
    if isinstance(node.token.value, float):
      return VariableType.REAL
    if isinstance(node.token.value, int):
      return VariableType.INTEGER
    if isinstance(node.token.value, str):
      return VariableType.STRING
    else:
      raise NotImplementedError("Invalid type")

  def _visit_assign(self, node: ASTNode) -> VariableType:
    left_type = self._visit_id(node)
    right_type = self.visit(node.children[0])
    if right_type != left_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == VariableType.VOID:
      self._error("Invalid type VOID", node)
    return VariableType.VOID

  def _visit_declaration(self, node: ASTNode):
    for child in node.children:
      var_name = child.token.value
      var_symbol = VarSymbol(var_name, VariableType(node.token.type.name))
      if self._current_scope.lookup(var_name, current_scope_only=True):
        self._error(f"Variable '{var_name}' already declared", child)
      self._current_scope.add(var_symbol)
    return VariableType.VOID

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
        VariableType(return_type.token.value.upper()),
        block_node=block,
        param_types=[],
    )
    self._current_func = Function(func_symbol, self._current_func)
    for param in params.children:
      self._visit_declaration(param)
      func_symbol.param_types.extend(
          [VariableType(param.token.type.name)] * len(param.children))
    return_type = self.visit(block)
    if func_symbol.return_type != return_type:
      self._error(
          f"Return type mismatch {self._current_func.func.return_type.name} and "
          f"{return_type.name}", node,)
    self._current_scope = self._current_scope.parent
    self._current_func = self._current_func.parent
    self._current_scope.add(func_symbol)
    return VariableType.VOID

  def _visit_return(self, node: ASTNode):
    if self._current_func is None:
      self._error("Return statement outside function", node)
    return_type = self.visit(node.children[0])
    if self._current_func.func.return_type != return_type:
      self._error(
          f"Return type mismatch {self._current_func.func.return_type.name} and "
          f"{return_type.name}", node,)
    return return_type

  def _visit_type(self, node: ASTNode) -> VariableType:
    return VariableType(node.token.value.upper())

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
    return func_symbol.return_type

  def _visit_control_flow(self, node: ASTNode):
    condition_type = self.visit(node.children[0])
    if condition_type != VariableType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self.visit(child)
    return VariableType.VOID

  def _visit_loop(self, node: ASTNode):
    condition_type = self.visit(node.children[0])
    if condition_type != VariableType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self.visit(child)
    return VariableType.VOID

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #
