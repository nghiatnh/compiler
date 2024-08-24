from compiler.ast_node import ASTNode, ASTNodeVisitor
from compiler.symbol_table import SymbolTable, VarSymbol, FuncSymbol
from compiler.constants import ASTNodeType
from compiler.constants import FunctionType
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


class Loop:
  """
  Loop
  ====
  """

  def __init__(self, parent: "Loop" = None) -> None:
    self._parent = parent

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
    self._current_loop = None

  def _error(self, message: str, node: ASTNode):
    raise SemanticError(
        f"{message}, line {node.token.line}, column {node.token.column}")

  def _enter_scope(self, scope: SymbolTable):
    self._current_scope = scope

  def _leave_scope(self):
    if self._current_scope is None:
      raise ValueError("Leave the empty scope")
    self._current_scope = self._current_scope.parent

  def _enter_function(self, function: Function):
    self._current_func = function

  def _leave_function(self):
    if self._current_func is None:
      raise ValueError("Leave the empty function")
    self._current_func = self._current_func.parent

  def _enter_loop(self, loop: Loop):
    self._current_loop = loop

  def _leave_loop(self):
    if self._current_loop is None:
      raise ValueError("Leave the empty loop")
    self._current_loop = self._current_loop.parent

  def _generic_visit(self, node: ASTNode) -> FunctionType:
    if node.type in ASTNodeType:
      for child in node.children:
        self.visit(child)
      return FunctionType.VOID
    return super()._generic_visit(node)

  # ========================================================================= #
  # Program                                                                   #
  # ========================================================================= #

  def _visit_program(self, node: ASTNode) -> FunctionType:
    global_scope = SymbolTable(node.token.value, 1)
    self._enter_scope(global_scope)
    self._generic_visit(node)
    self._leave_scope()
    return FunctionType.VOID

  def _visit_block(self, node: ASTNode) -> FunctionType:
    var_decl, *func_decls, statements = node.children
    self.visit(var_decl)
    for func_decl in func_decls:
      self.visit(func_decl)
    return self._visit_statements(statements)

  # ========================================================================= #
  # Variables                                                                 #
  # ========================================================================= #

  def _visit_declaration(self, node: ASTNode) -> FunctionType:
    for child in node.children:
      var_name = child.token.value
      var_symbol = VarSymbol(var_name, FunctionType(node.token.type.name))
      if self._current_scope.lookup(var_name, current_scope_only=True):
        self._error(f"Variable '{var_name}' already declared", child)
      self._current_scope.add(var_symbol)
    return FunctionType.VOID

  def _visit_assign(self, node: ASTNode) -> FunctionType:
    left_type = self._visit_id(node)
    right_type = self.visit(node.children[0])
    if right_type != left_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == FunctionType.VOID:
      self._error("Invalid type VOID", node)
    return FunctionType.VOID

  def _visit_type(self, node: ASTNode) -> FunctionType:
    return FunctionType(node.token.value.upper())

  # ========================================================================= #
  # Functions                                                                 #
  # ========================================================================= #

  def _visit_func_decl(self, node: ASTNode) -> FunctionType:
    func_name = node.token.value
    if self._current_scope.lookup(func_name, current_scope_only=True):
      self._error(f"Function '{func_name}' already declared", node)
    func_scope = SymbolTable(
        func_name, self._current_scope.level + 1,
        self._current_scope,
    )
    self._enter_scope(func_scope)
    params, return_type, block = node.children
    func_symbol = FuncSymbol(
        func_name, FunctionType(return_type.token.value.upper()),
        block_node=block, param_types=[],
    )
    self._enter_function(Function(func_symbol, self._current_func))
    for param in params.children:
      self._visit_declaration(param)
      patam_types = [FunctionType(param.token.type.name)] * len(param.children)
      func_symbol.param_types.extend(patam_types)
    if self._current_scope.parent is not None:
      self._current_scope.parent.add(func_symbol)
    return_type = self.visit(block)
    if func_symbol.return_type != return_type:
      self._error(
          (f"Return type mismatch {self._current_func.func.return_type.name} and "
           f"{return_type.name}"), node,
      )
    self._leave_function()
    self._leave_scope()
    return FunctionType.VOID

  def _visit_call(self, node: ASTNode) -> FunctionType:
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

  def _visit_return(self, node: ASTNode) -> FunctionType:
    if self._current_func is None:
      self._error("Return statement outside function", node)
    return_type = self.visit(node.children[0])
    if self._current_func.func.return_type != return_type:
      self._error(
          f"Return type mismatch {self._current_func.func.return_type.name} and "
          f"{return_type.name}", node,)
    return return_type

  # ========================================================================= #
  # Statements                                                                #
  # ========================================================================= #

  def _visit_binary_op(self, node: ASTNode) -> FunctionType:
    left_type = self.visit(node.children[0])
    right_type = self.visit(node.children[1])
    if left_type != right_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == FunctionType.VOID:
      self._error("Invalid type VOID", node)

    # Only operate AND/OR on BOOLEAN type
    if node.token.type in (TokenType.AND, TokenType.OR):
      if left_type != FunctionType.BOOLEAN:
        self._error(f"Invalid type {left_type.name}", node)
      return FunctionType.BOOLEAN

    # Can not operate comparision on BOOLEAN type
    if node.token.type in (
        TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.LE,
        TokenType.GT, TokenType.GE
    ):
      if left_type == TokenType.BOOLEAN:
        self._error(f"Invalid type {left_type.name}", node)
      return FunctionType.BOOLEAN

    # Can not operate ADD on BOOLEAN type
    if node.token.type == TokenType.PLUS and left_type == TokenType.BOOLEAN:
      self._error(f"Invalid type {left_type.name}", node)

    # Only operate DIV/MOD on INTEGER type
    if node.token.type in [TokenType.INTEGER_DIV, TokenType.INTEGER_MOD]:
      if left_type != TokenType.INTEGER:
        self._error(f"Invalid type {left_type.name}", node)

    # Only operate DIVIDE on REAL type
    if node.token.type == TokenType.SLASH:
      if left_type != TokenType.REAL:
        self._error(f"Invalid type {left_type.name}", node)

    # Only operate SUB/MUL on INTEGER and REAL types
    if node.token.type == [TokenType.STAR, TokenType.MINUS]:
      if left_type not in [TokenType.REAL, TokenType.INTEGER]:
        self._error(f"Invalid type {left_type.name}", node)
    return left_type

  def _visit_unary_op(self, node: ASTNode) -> FunctionType:
    return_type = self.visit(node.children[0])
    if return_type == FunctionType.VOID:
      self._error("Invalid type VOID", node)

    # Only operate NOT on BOOLEAN type
    if node.token.type == TokenType.NOT:
      if return_type != FunctionType.BOOLEAN:
        self._error(f"Invalid type {return_type.name}", node)
      return FunctionType.BOOLEAN

    # Only operate PLUS/MINUS on INTEGER and REAL type
    if return_type not in [FunctionType.REAL, FunctionType.INTEGER]:
      self._error(f"Invalid type {return_type.name}", node)
    return return_type

  def _visit_statements(self, node: ASTNode) -> FunctionType:
    for child in node.children:
      if child.type in [
          ASTNodeType.RETURN,
          ASTNodeType.BREAK,
          ASTNodeType.CONTINUE,
      ]:
        return self.visit(child)
      self.visit(child)
    return FunctionType.VOID

  def _visit_id(self, node: ASTNode) -> FunctionType:
    var_name = node.token.value
    var_symbol = self._current_scope.lookup(var_name)
    if var_symbol is None:
      self._error(f"Variable undefined '{var_name}'", node)
    if not isinstance(var_symbol, VarSymbol):
      self._error(f"'{var_name}' is not a variable", node)
    return var_symbol.var_type

  def _visit_value(self, node: ASTNode) -> FunctionType:
    if isinstance(node.token.value, bool):
      return FunctionType.BOOLEAN
    if isinstance(node.token.value, float):
      return FunctionType.REAL
    if isinstance(node.token.value, int):
      return FunctionType.INTEGER
    if isinstance(node.token.value, str):
      return FunctionType.STRING
    raise NotImplementedError(f"Invalid type {type(node.token.value)}")

  # ========================================================================= #
  # Control flow                                                              #
  # ========================================================================= #

  def _visit_control_flow(self, node: ASTNode):
    condition_type = self.visit(node.children[0])
    if condition_type != FunctionType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self.visit(child)
    return FunctionType.VOID

  # ========================================================================= #
  # Loop                                                                      #
  # ========================================================================= #

  def _visit_loop(self, node: ASTNode):
    self._enter_loop(Loop(self._current_loop))
    condition_type = self.visit(node.children[0])
    if condition_type != FunctionType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self.visit(child)
    self._leave_loop()
    return FunctionType.VOID

  def _visit_jump(self, node: ASTNode):
    if self._current_loop is None:
      self._error(f"{node.type.name} statement outside the loop", node)
    return FunctionType.VOID

  def _visit_break(self, node: ASTNode):
    self._visit_jump(node)

  def _visit_continue(self, node: ASTNode):
    self._visit_jump(node)

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #
