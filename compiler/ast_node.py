from typing import List, Any
import graphviz

from compiler.token import Token
from compiler.constants import ASTNodeType


class ASTNode:
  """
  ASTNode
  =======
  The ASTNode class represents a node in the abstract syntax tree. It contains
  a token and a list of children nodes. The token represents the node's value
  and the children represent the node's children.
  """

  def __init__(
      self,
      type: ASTNodeType,
      token: Token,
      children: List["ASTNode"] = None,
  ):
    self._type = type
    self._token = token
    self._children = children or []

  def _add_node(self, dot: graphviz.Digraph):
    if self.token and self.token.value:
      dot.node(str(id(self)), f"{self.type.name}: {self.token.value}")
    else:
      dot.node(str(id(self)), f"{self.type.name}")
    for child in self.children:
      child._add_node(dot)
      dot.edge(str(id(self)), str(id(child)))

  # ========================================================================= #
  # Properties                                                                #
  # ========================================================================= #

  @property
  def token(self) -> Token:
    return self._token

  @property
  def children(self) -> List["ASTNode"]:
    return self._children

  @property
  def type(self) -> ASTNodeType:
    return self._type

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def print_tree(self, filename: str):
    """
    Print the abstract syntax tree to a file using graphviz.
    """
    dot = graphviz.Digraph()
    self._add_node(dot)
    dot.render(filename, format="png", view=True)


class ASTNodeVisitor:
  """
  ASTNodeVisitor
  ==============
  The ASTNodeVisitor class is an abstract class that defines the interface for
  visiting the nodes in the abstract syntax tree.
  """

  def _generic_visit(self, node: ASTNode) -> None:
    """
    Generic visit method. This method will be called if a specific visit method
    is not implemented for the given node's type.
    """
    raise NotImplementedError(
        f"Method visit_{node.type.name.lower()} not implemented"
    )

  # ========================================================================= #
  # Public methods                                                            #
  # ========================================================================= #

  def visit(cls, node: ASTNode) -> Any:
    """
    Visit the given node. This method will call the appropriate visit method
    based on the node's type.
    """
    method_name = f"_visit_{node.type.name.lower()}"
    visit_fn = getattr(cls, method_name, cls._generic_visit)
    return visit_fn(node)
