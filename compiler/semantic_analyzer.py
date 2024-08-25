from compiler.ast_node import ASTNode
from compiler.symbol_table import SymbolTable, VarSymbol, FuncSymbol
from compiler.constants import ASTNodeType
from compiler.constants import ReturnType
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
  Function class is a class that is used to represent a function in the symbol
  table. It contains a function symbol and a reference to the parent function.
  """

  def __init__(self, symbol: FuncSymbol, parent: "Function" = None) -> None:
    self._symbol = symbol
    self._parent = parent

  @property
  def symbol(self) -> FuncSymbol:
    return self._symbol

  @property
  def parent(self) -> "Function":
    return self._parent


class Loop:
  """
  Loop
  ====
  Loop class is a class that is used to represent a loop in the symbol table.
  It contains a reference to the parent loop.
  """

  def __init__(self, parent: "Loop" = None) -> None:
    self._parent = parent

  @property
  def parent(self) -> "Loop":
    return self._parent


class SemanticAnalyzer:
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
    if self._current_scope is not None:
      self._current_scope.children.append(scope)
    scope.parent = self._current_scope
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

  def _generic_visit(self, node: ASTNode) -> ReturnType:
    if node.type in ASTNodeType:
      for child in node.children:
        self._visit(child)
      return ReturnType.VOID
    raise NotImplementedError(f"Invalid node type {node.type}")

  def _visit(self, node: ASTNode) -> ReturnType:
    visit_fn = getattr(
        self, f"_visit_{node.type.name.lower()}", self._generic_visit)
    return visit_fn(node)

  # ========================================================================= #
  # Program                                                                   #
  # ========================================================================= #

  def _visit_program(self, node: ASTNode) -> ReturnType:
    program_scope = SymbolTable(node.token.value, 1, self._current_scope)
    self._enter_scope(program_scope)
    self._generic_visit(node)
    self._leave_scope()
    return ReturnType.VOID

  def _visit_block(self, node: ASTNode) -> ReturnType:
    var_decl, *func_decls, statements = node.children
    self._visit(var_decl)
    for func_decl in func_decls:
      self._visit(func_decl)
    return self._visit_statements(statements)

  # ========================================================================= #
  # Variables                                                                 #
  # ========================================================================= #

  def _visit_declaration(self, node: ASTNode) -> ReturnType:
    for child in node.children:
      var_name = child.token.value
      var_symbol = VarSymbol(var_name, ReturnType(node.token.type.name))
      if self._current_scope.lookup(var_name, current_scope_only=True):
        self._error(f"Variable '{var_name}' already declared", child)
      self._current_scope.add(var_symbol)
    return ReturnType.VOID

  def _visit_assign(self, node: ASTNode) -> ReturnType:
    left_type = self._visit_id(node)
    right_type = self._visit(node.children[0])
    if right_type != left_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == ReturnType.VOID:
      self._error("Invalid type VOID", node)
    return ReturnType.VOID

  def _visit_type(self, node: ASTNode) -> ReturnType:
    return ReturnType(node.token.value.upper())

  # ========================================================================= #
  # Functions                                                                 #
  # ========================================================================= #

  def _visit_func_decl(self, node: ASTNode) -> ReturnType:
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
        func_name, ReturnType(return_type.token.value.upper()),
        block_node=block, param_types=[],
    )
    self._enter_function(Function(func_symbol, self._current_func))
    for param in params.children:
      self._visit_declaration(param)
      patam_types = [ReturnType(param.token.type.name)] * len(param.children)
      func_symbol.param_types.extend(patam_types)
    if self._current_scope.parent is not None:
      self._current_scope.parent.add(func_symbol)
    return_type = self._visit(block)
    if func_symbol.return_type != return_type:
      self._error(
          (f"Return type mismatch {func_symbol.return_type.name} and "
           f"{return_type.name}"), node,
      )
    self._leave_function()
    self._leave_scope()
    return ReturnType.VOID

  def _visit_call(self, node: ASTNode) -> ReturnType:
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

  def _visit_return(self, node: ASTNode) -> ReturnType:
    if self._current_func is None:
      self._error("Return statement outside function", node)
    return_type = self._visit(node.children[0])
    if self._current_func.symbol.return_type != return_type:
      self._error(
          f"Return type mismatch {self._current_func.symbol.return_type.name} "
          f"and {return_type.name}", node,)
    return return_type

  # ========================================================================= #
  # Statements                                                                #
  # ========================================================================= #

  def _visit_binary_op(self, node: ASTNode) -> ReturnType:
    left_type = self._visit(node.children[0])
    right_type = self._visit(node.children[1])
    if left_type != right_type:
      self._error(f"Type mismatch {left_type.name} and {right_type.name}", node)
    if left_type == ReturnType.VOID:
      self._error("Invalid type VOID", node)

    # Only operate AND/OR on BOOLEAN type
    if node.token.type in (TokenType.AND, TokenType.OR):
      if left_type != ReturnType.BOOLEAN:
        self._error(f"Invalid type {left_type.name}", node)
      return ReturnType.BOOLEAN

    # Can not operate comparision on BOOLEAN type
    if node.token.type in (
        TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.LE,
        TokenType.GT, TokenType.GE
    ):
      if left_type == TokenType.BOOLEAN:
        self._error(f"Invalid type {left_type.name}", node)
      return ReturnType.BOOLEAN

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

  def _visit_unary_op(self, node: ASTNode) -> ReturnType:
    return_type = self._visit(node.children[0])
    if return_type == ReturnType.VOID:
      self._error("Invalid type VOID", node)

    # Only operate NOT on BOOLEAN type
    if node.token.type == TokenType.NOT:
      if return_type != ReturnType.BOOLEAN:
        self._error(f"Invalid type {return_type.name}", node)
      return ReturnType.BOOLEAN

    # Only operate PLUS/MINUS on INTEGER and REAL type
    if return_type not in [ReturnType.REAL, ReturnType.INTEGER]:
      self._error(f"Invalid type {return_type.name}", node)
    return return_type

  def _visit_statements(self, node: ASTNode) -> ReturnType:
    for child in node.children:
      if child.type in [
          ASTNodeType.RETURN,
          ASTNodeType.BREAK,
          ASTNodeType.CONTINUE,
      ]:
        return self._visit(child)
      self._visit(child)
    return ReturnType.VOID

  def _visit_id(self, node: ASTNode) -> ReturnType:
    var_name = node.token.value
    var_symbol = self._current_scope.lookup(var_name)
    if var_symbol is None:
      self._error(f"Variable undefined '{var_name}'", node)
    if not isinstance(var_symbol, VarSymbol):
      self._error(f"'{var_name}' is not a variable", node)
    return var_symbol.var_type

  def _visit_value(self, node: ASTNode) -> ReturnType:
    if isinstance(node.token.value, bool):
      return ReturnType.BOOLEAN
    if isinstance(node.token.value, float):
      return ReturnType.REAL
    if isinstance(node.token.value, int):
      return ReturnType.INTEGER
    if isinstance(node.token.value, str):
      return ReturnType.STRING
    raise NotImplementedError(f"Invalid type {type(node.token.value)}")

  # ========================================================================= #
  # Control flow                                                              #
  # ========================================================================= #

  def _visit_control_flow(self, node: ASTNode):
    condition_type = self._visit(node.children[0])
    if condition_type != ReturnType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self._visit(child)
    return ReturnType.VOID

  # ========================================================================= #
  # Loop                                                                      #
  # ========================================================================= #

  def _visit_loop(self, node: ASTNode):
    self._enter_loop(Loop(self._current_loop))
    condition_type = self._visit(node.children[0])
    if condition_type != ReturnType.BOOLEAN:
      self._error(f"Invalid condition type {condition_type.name}", node)
    for child in node.children[1:]:
      self._visit(child)
    self._leave_loop()
    return ReturnType.VOID

  def _visit_jump(self, node: ASTNode):
    if self._current_loop is None:
      self._error(f"{node.type.name} statement outside the loop", node)
    return ReturnType.VOID

  def _visit_break(self, node: ASTNode):
    self._visit_jump(node)

  def _visit_continue(self, node: ASTNode):
    self._visit_jump(node)

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def analyze(self, root: ASTNode) -> SymbolTable:
    """
    Analyze the abstract syntax tree. This method will traverse the tree and
    check for semantic errors such as undeclared variables and functions and
    type mismatches.
    """
    global_scope = SymbolTable("global", 0)
    self._enter_scope(global_scope)
    self._visit(root)
    self._leave_scope()
    return global_scope
