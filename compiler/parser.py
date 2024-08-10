class LoopBreak(Exception):
  pass


class LoopContinue(Exception):
  pass


def parse_expr(s: str, idx: int):
  idx = skip_whitespace(s, idx)
  if s[idx] == "(":
    idx += 1
    l = []
    while True:
      idx = skip_whitespace(s, idx)
      if idx >= len(s):
        raise Exception("unbalanced parenthesis")
      if s[idx] == ")":
        idx += 1
        break
      idx, v = parse_expr(s, idx)
      l.append(v)
    return idx, l
  elif s[idx] == ")":
    raise Exception("bad parenthesis")
  else:
    start = idx
    while idx < len(s) and (not s[idx].isspace()) and s[idx] not in "()":
      idx += 1
    if start == idx:
      raise Exception("empty expression")
    return idx, parse_atom(s[start:idx])


def skip_whitespace(s: str, idx: int):
  while True:
    save = idx
    # skip whitespace
    while idx < len(s) and s[idx].isspace():
      idx += 1
    # skip comment
    if idx + 1 < len(s) and s[idx] == ";" and s[idx + 1] == ";":
      idx += 2
      while idx < len(s) and s[idx] != "\n":
        idx += 1
    # if no progress, break
    if idx == save:
      break
  return idx


def parse_atom(s):
  import json
  try:
    return ["val", json.loads(s)]
  except json.JSONDecodeError:
    return s


def pl_parse(s):
  idx, node = parse_expr(s, 0)
  idx = skip_whitespace(s, idx)
  if idx < len(s):
    raise ValueError("traling garbage")
  return node


def pl_parse_main(s):
  return pl_parse("(def (main int) () (do " + s + "))")
