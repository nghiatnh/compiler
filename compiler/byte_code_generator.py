from typing import Dict, Tuple

from compiler.ast_node import ASTNode
from compiler.byte_code import ByteCode
from compiler.symbol_table import SymbolTable
from compiler.constants import ASTNodeType
from compiler.constants import ReturnType
from compiler.constants import TokenType
from compiler.constants import OpCode
from compiler.constants import BinaryOp


class Loop:
  """
  Loop
  ====
  Loop class to represent a loop in the code generator.
  """

  def __init__(self, start: int, end: int, parent: "Loop") -> None:
    self.start = start
    self.end = end
    self.parent = parent


class ByteCodeGenerator:
  """
  ByteCodeGenerator
  =================
  ByteCodeGenerator is a class that is used to generate code from the abstract
  syntax tree. The code generator will traverse the tree and generate code for
  each node in the tree.
  """

  def __init__(self, global_scope: SymbolTable) -> None:
    self._global_scope = global_scope
    self._scope: SymbolTable = None
    self._scopes = self._flat_scopes(global_scope)
    self._loop = None

  # ========================================================================= #
  # Private methods                                                           #
  # ========================================================================= #

  def _flat_scopes(
      self, scope: SymbolTable
  ) -> Dict[Tuple[int, str], SymbolTable]:
    scopes = {
        (scope.level, scope.name): scope
    }
    for child in scope.children:
      scopes.update(self._flat_scopes(child))
    return scopes

  def _enter_scope(self, level: int, name: str):
    self._scope = self._scopes[(level, name)]

  def _leave_scope(self):
    if self._scope is None:
      raise ValueError("Leave the empty scope")
    parent = self._scope.parent
    if parent is not None:
      self._enter_scope(parent.level, parent.name)

  def _enter_loop(self, start: int, end: int):
    self._loop = Loop(start, end, self._loop)

  def _leave_loop(self):
    if self._loop is None:
      raise ValueError("Leave the empty loop")
    self._loop = self._loop.parent

  def _add_code(self, opcode: OpCode, operands: list):
    self._scope.code.append(ByteCode(opcode, operands))

  def _move_to(self, var: int, dst: int):
    if dst != var:
      self._add_code(OpCode.MOV, [dst, var])
    return dst

  def _generic_generate(self, node: ASTNode) -> int:
    if node.type in ASTNodeType:
      for child in node.children:
        self._generate(child)
      return -1
    raise NotImplementedError(f"Invalid node type {node.type}")

  def _generate(self, node: ASTNode) -> int:
    visit_fn = getattr(
        self, f"_generate_{node.type.name.lower()}", self._generic_generate)
    return visit_fn(node)

  # ========================================================================= #
  # Code Generation methods                                                   #
  # ========================================================================= #

  # ========================================================================= #
  # Program                                                                   #
  # ========================================================================= #

  def _generate_program(self, node: ASTNode) -> int:
    self._enter_scope(1, node.token.value)
    self._generic_generate(node)
    self._leave_scope()
    return -1

  def _generate_block(self, node: ASTNode) -> int:
    var_decl, *func_decls, statements = node.children
    self._generate(var_decl)
    for func_decl in func_decls:
      self._generate(func_decl)
    return self._generate_statements(statements)

  # ========================================================================= #
  # Variables                                                                 #
  # ========================================================================= #

  def _generate_assign(self, node: ASTNode) -> int:
    var_name = node.token.value
    level, var_symbol = self._scope.lookup(var_name)
    rindex = self._generate(node.children[0])
    if level == self._scope.level:
      return self._move_to(rindex, var_symbol.index)
    self._add_code(OpCode.SET_ENV, [level, var_symbol.index, rindex])
    return self._move_to(rindex, self._scope.new_var())

  def _generate_type(self, node: ASTNode) -> ReturnType:
    return ReturnType(node.token.value.upper())

  # ========================================================================= #
  # Functions                                                                 #
  # ========================================================================= #

  def _generate_func_decl(self, node: ASTNode) -> int:
    func_name = node.token.value
    self._enter_scope(self._scope.level + 1, func_name)
    _, _, block = node.children
    self._generate(block)
    self._leave_scope()
    return -1

  def _generate_call(self, node: ASTNode) -> int:
    func_name = node.token.value
    level, func_symbol = self._scope.lookup(func_name)
    for child in node.children:
      save = self._scope.stack
      rindex = self._generate(child)
      self._scope.stack = save
      self._move_to(rindex, self._scope.new_var())

    self._scope.stack -= len(node.children)

    rtype = func_symbol.type
    func_index = next(
        i for i, x in enumerate(self._scopes)
        if (x[0], x[1].upper()) == (level + 1, func_name.upper())
    ) - 1
    self._add_code(
        OpCode.CALL,
        [func_index, self._scope.stack, self._scope.level, level + 1]
    )
    return -1 if rtype == ReturnType.VOID else self._scope.new_var()

  def _generate_syscall(self, node: ASTNode) -> int:
    dst = self._scope.new_var()
    args = [dst]
    for child in node.children:
      save = self._scope.stack
      rindex = self._generate(child)
      self._scope.stack = save
      args.append(self._scope.new_var())
      self._move_to(rindex, args[-1])

    self._scope.stack -= len(node.children)

    self._add_code(OpCode.SYSCALL, args)
    return dst

  def _generate_return(self, node: ASTNode) -> int:
    rindex = self._generate(node.children[0])
    self._add_code(OpCode.RET, [rindex])
    return rindex

  # ========================================================================= #
  # Statements                                                                #
  # ========================================================================= #

  def _generate_binary_op(self, node: ASTNode) -> int:
    lindex = self._generate(node.children[0])
    rindex = self._generate(node.children[1])
    dst = self._scope.new_var()
    self._add_code(
        OpCode.BINOP, [BinaryOp(node.token.type.value), lindex, rindex, dst])
    return dst

  def _generate_mov_ptr(self, node: ASTNode) -> int:
    lindex = self._generate(node.children[0])
    rindex = self._generate(node.children[1])
    dst = self._scope.new_var()
    sign = 1 if node.token.type == TokenType.PLUS else -1
    self._add_code(OpCode.LEA, [lindex, rindex, sign, dst])
    return dst

  def _generate_unary_op(self, node: ASTNode) -> int:
    rindex = self._generate(node.children[0])
    dst = self._scope.new_var()
    if node.token.type == TokenType.MINUS:
      self._add_code(OpCode.NEG, [rindex, dst])
    elif node.token.type == TokenType.PLUS:
      return rindex
    else:
      self._add_code(OpCode.NOT, [rindex, dst])
    return dst

  def _generate_statements(self, node: ASTNode) -> int:
    for child in node.children:
      if child.type in [
          ASTNodeType.RETURN,
          ASTNodeType.BREAK,
          ASTNodeType.CONTINUE,
      ]:
        return self._generate(child)
      self._generate(child)
    return -1

  def _generate_id(self, node: ASTNode) -> int:
    var_name = node.token.value
    level, var_symbol = self._scope.lookup(var_name)
    dst = var_symbol.index
    if level != self._scope.level:
      dst = self._scope.new_var()
      self._add_code(OpCode.GET_ENV, [level, var_symbol.index, dst])
    return dst

  def _generate_value(self, node: ASTNode) -> ReturnType:
    dst = self._scope.new_var()
    self._add_code(OpCode.CONST, [node.token.value, dst])
    return dst

  # ========================================================================= #
  # Pointers                                                                  #
  # ========================================================================= #

  def _generate_peek(self, node: ASTNode) -> int:
    rindex = self._generate(node.children[0])
    dst = self._scope.new_var()
    self._add_code(OpCode.PEEK, [rindex, dst])
    return dst

  def _generate_poke(self, node: ASTNode) -> int:
    rindex = self._generate(node.children[0])
    value_index = self._generate(node.children[1])
    self._add_code(OpCode.POKE, [rindex, value_index])
    return -1

  def _generate_ref(self, node: ASTNode) -> int:
    rindex = self._generate(node.children[0])
    dst = self._scope.new_var()
    self._add_code(OpCode.REF, [rindex, dst])
    return dst

  def _generate_cast(self, node: ASTNode) -> int:
    return self._generate(node.children[0])

  # ========================================================================= #
  # Control flow                                                              #
  # ========================================================================= #

  def _generate_control_flow(self, node: ASTNode):
    cond, yes, *no = node.children
    l_true = self._scope.new_label()
    l_false = self._scope.new_label()
    self._add_code(OpCode.JMPF, [self._generate(cond), l_false])
    self._generate(yes)
    if no:
      self._add_code(OpCode.JMP, l_true)
    self._scope.set_label(l_false, len(self._scope.code))
    if no:
      self._generate(no)
    self._scope.set_label(l_true, len(self._scope.code))
    return -1

  # ========================================================================= #
  # Loop                                                                      #
  # ========================================================================= #

  def _generate_loop(self, node: ASTNode):
    l_start = self._scope.new_label()
    l_end = self._scope.new_label()
    self._enter_loop(l_start, l_end)
    cond, statement = node.children
    self._scope.set_label(l_start, len(self._scope.code))
    self._add_code(OpCode.JMPF, [self._generate(cond), l_end])
    self._generate(statement)
    self._add_code(OpCode.JMP, [l_start])
    self._scope.set_label(l_end, len(self._scope.code))
    self._leave_loop()
    return -1

  def _generate_break(self, _: ASTNode) -> int:
    self._add_code(OpCode.JMP, [self._loop.end])
    return -1

  def _generate_continue(self, _: ASTNode) -> int:
    self._add_code(OpCode.JMP, [self._loop.start])
    return -1

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def generate(self, root: ASTNode) -> SymbolTable:
    """
    Generate byte code from the abstract syntax tree.
    """
    self._enter_scope(self._global_scope.level, self._global_scope.name)
    self._generate(root)
    self._leave_scope()
    return self._scopes[(self._global_scope.level, self._global_scope.name)]
