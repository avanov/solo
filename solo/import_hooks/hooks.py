""" Based on
https://greentreesnakes.readthedocs.io
"""
import ast


class AstTransformer(ast.NodeTransformer):
    pass


def apply_transformers(tree):
    tree = AstTransformer().visit(tree)
    # Add lineno & col_offset to possibly modified nodes
    ast.fix_missing_locations(tree)
    return tree
