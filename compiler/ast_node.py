from typing import List
import graphviz

from compiler.token import Token
from compiler.constants import ASTNodeType
from compiler.constants import FunctionType


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
      node_type: ASTNodeType,
      token: Token,
      children: List["ASTNode"] = None,
  ):
    self._type = node_type
    self._token = token
    self._children = children or []

  def __str__(self) -> str:
    return f"<ASTNode {self.type.name}: {self.token.value}>"

  def __repr__(self) -> str:
    return self.__str__()

  def add_node(self, dot: graphviz.Digraph):
    if self.token and self.token.value is not None:
      dot.node(str(id(self)), f"{self.type.name}: {self.token.value}")
    else:
      dot.node(str(id(self)), f"{self.type.name}")
    for child in self.children:
      child.add_node(dot)
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

  def render_tree(self, filename: str):
    """
    Render the abstract syntax tree to a file using graphviz.
    """
    dot = graphviz.Digraph()
    self.add_node(dot)
    dot.render(filename, format="png", view=True)


class ASTNodeVisitor:
  """
  ASTNodeVisitor
  ==============
  The ASTNodeVisitor class is an abstract class that defines the interface for
  visiting the nodes in the abstract syntax tree.
  """

  def _generic_visit(self, node: ASTNode) -> FunctionType:
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

  def visit(self, node: ASTNode) -> FunctionType:
    """
    Visit the given node. This method will call the appropriate visit method
    based on the node's type.
    """
    method_name = f"_visit_{node.type.name.lower()}"
    visit_fn = getattr(self, method_name, self._generic_visit)
    return visit_fn(node)
