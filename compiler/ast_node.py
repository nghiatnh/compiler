from typing import List
import graphviz

from compiler.token import Token


class ASTNode:
  """
  ASTNode
  =======
  The ASTNode class represents a node in the abstract syntax tree. It contains
  a token and a list of children nodes. The token represents the node's value
  and the children represent the node's children.
  """

  def __init__(self, token: Token, children: List["ASTNode"] = None):
    self._token = token
    self._children = children or []

  def _add_node(self, dot: graphviz.Digraph):
    dot.node(str(id(self)), f"{self.token.type.name}: {self.token.value}")
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
  def type(self):
    return self._token.type

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
