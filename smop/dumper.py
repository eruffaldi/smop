# smop -- Simple Matlab to Python compiler
# Copyright 2011-2014 Victor Leikehman

"""
Calling conventions:

call site:  nargout=N is passed if and only if N > 1
func decl:  nargout=1 must be declared if function may return
            more than one return value.  Otherwise optional.
return value:  return (x,y,z)[:nargout] or return x
"""

import logging
logger = logging.getLogger(__name__)
import node,options
from node import extend
from lxml import etree

indent = " "*4

optable = {
    "!" : "not",
    "~" : "not",
    "~=": "!=",
    "|" : "or",
    "&" : "and",
    "||": "or",
    "&&": "and",
    "^" : "**",
    ".^": "**",
    "./": "/",
    ".*": "*",
    }

def dumper(t,*args):
    return t._dumper(*args)

@extend(node.matrix)
def _dumper(self,level=0):
    # TODO empty array has shape of 0 0 in matlab
    # size([])
    # 0 0
    e = etree.Element("matrix")
    for t in self.args:
        e.append(t._dumper())
    return e

@extend(node.cellarrayref)
def _dumper(self,level=0):
    e = etree.Element("cellarrayref")
    e.append(self.func_expr._dumper())
    e.append(self.args._dumper())
    return e

@extend(node.cellarray)
def _dumper(self,level=0):
    e = etree.Element("cellarray")
    e.append(self.args._dumper())
    return e

#@extend(node.concat_list)
#def _dumper(self,level=0):
#    return ";".join([t._dumper() for t in self])

@extend(node.ravel)
def _dumper(self,level=0):
    e = etree.Element("ravel")
    e.append(self.args[0]._dumper())
    return e

@extend(node.transpose)
def _dumper(self,level=0):
    e = etree.Element("transpose")
    e.append(self.args[0]._dumper())
    return e

@extend(node.expr_stmt)
def _dumper(self,level=0):
    return self.expr._dumper()

@extend(node.return_stmt)
def _dumper(self,level=0):
    e = etree.Element("return")
    if self.ret:
        e.append(self.ret._dumper())
    return e

@extend(node.continue_stmt)
def _dumper(self,level=0):
    return etree.Element("continue")

@extend(node.global_stmt)
def _dumper(self,level=0):
    e = etree.Element("global")
    for t in self.global_list:
        e.append(t._dumper())
    return e

@extend(node.global_list)
def _dumper(self,level=0):
    e = etree.Element("global_list")
    for t in self:
        e.append(t._dumper())
    return e

@extend(node.break_stmt)
def _dumper(self,level=0):
    return etree.Element("break")

@extend(node.string)
def _dumper(self,level=0):
    e = etree.Element("string")
    e.set("value",str(self.value))
    return e

@extend(node.number)
def _dumper(self,level=0):
    e = etree.Element("number")
    e.set("value",str(self.value))
    return e

@extend(node.logical)
def _dumper(self,level=0):
    e = etree.Element("logical")
    e.set("value",str(self.value))
    return e
    
# @extend(node.range)
# def _dumper(self,level=0):
#     i = node.ident.new("I")
#     return "[ (%s, %s=%s,%s) ]" % (i,i,self.args[0],self.args[1])

@extend(node.add)
def _dumper(self,level=0):
    e = etree.Element("add")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return e

@extend(node.sub)
def _dumper(self,level=0):
    e = etree.Element("sub")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return e

@extend(node.expr)
def _dumper(self,level=0):
    e = etree.Element("expr_op")
    e.set("op",self.op)
    for t in self.args:
        e.append(t._dumper())
    return e


@extend(node.arrayref)
def _dumper(self,level=0):
    e = etree.Element("arrayref")
    e.append(self.func_expr._dumper())
    e.append(self.args._dumper())
    return e
    

@extend(node.funcall)
def _dumper(self,level=0):
    e = etree.Element("funcall")
    ce = etree.Element("expr")
    ce.append(self.func_expr._dumper())
    e.append(ce)
    ce = etree.Element("args")
    ce.append(self.args._dumper())
    e.append(ce)
    if self.nargout is not None:
        e.set("nargout",str(self.nargout))
    return e

@extend(node.let)
def _dumper(self,level=0):
    e = etree.Element("let")
    ce = etree.Element("target")
    ce.append(self.ret._dumper(level+1))
    e.append(ce)
    ce = etree.Element("value")
    ce.append(self.args._dumper())
    e.append(ce)
    return e

@extend(node.expr_list)
def _dumper(self,level=0):
    e = etree.Element("expr_list")
    for t in self:
        e.append(t._dumper())
    return e

@extend(node.concat_list)
def _dumper(self,level=0):
    e = etree.Element("concat_list")
    for t in self:
        e.append(t._dumper())
    return e

# @extend(node.call_stmt)
# def _dumper(self,level=0):
#     return "CALL %s(%s,%s)" % (self.func_expr._dumper(),
#                                self.args._dumper(),
# self.ret._dumper())

fortran_type = {
    '@': '***',
    'd': 'DOUBLE PRECISION',
    'i': 'INTEGER',
    'l': 'LOGICAL',
    'c': 'CHARACTER',
}

# def decl__dumper(i):
#     assert isinstance(i,ident)
#     try:
#         if i._rank() == 0:
#             return "%s :: %s\n" % (fortran_type[i._type()],
#                                    i)
#         return ("%s,DIMENSION(%s),ALLOCATABLE :: %s\n" % 
#                 (fortran_type[i._type()],
#                  ",".join([":" for j in range(i._rank())]), i))
#     except:
#         return "??? :: %s\n" % i
@extend(node.function)
def _dumper(self,level=0):
    e = etree.Element("function")
    ce = etree.Element("head")
    ce.append(self.head._dumper(level))
    e.append(ce)
    ce = etree.Element("body")
    ce.append(self.body._dumper(level+1))
    e.append(ce)
    return e
        

# Sometimes variable names collide with _python reserved
# words and constants.  We handle this in the _dumper rather than in
# the lexer, to keep the target language separate from
# the lexer code.
reserved = set(
    """
    abs and apply as assert basestring bin bool break buffer bytearray
    callable chr class classmethod cmp coerce compile complex continue copyright
    credits def del delattr dict dir divmod elif Ellipsis else enumerate eval
    except exec execfile exit False file filter finally float for format from
    frozenset getattr global globals hasattr hash help hex id if import __import__
    in input int intern is isinstance issubclass iter lambda len license list
    locals long map memoryview next None not not NotImplemented object oct
    open or ord pass pow print property quit raise range raw_input reduce reload
    repr return reversed round set setattr slice sorted staticmethod str sum super
    True try tuple type unichr unicode vars while with xrange yield zip struct
    """.split())

@extend(node.ident)
def _dumper(self,level=0):
    e = etree.Element("ident")
    e.set("name",self.name)
    return e

@extend(node.stmt_list)
def _dumper(self,level=0):
    e = etree.Element("stmt_list")
    for t in self:
        e.append(t._dumper(level))
    return e

@extend(node.func_decl)
def _dumper(self,level=0):
    #ident ret args decl_list use_nargin
    e = etree.Element("func_decl")
    e.set("name",self.ident.name)
    ce = etree.Element("args")
    for a in self.args:
        cee = etree.Element("arg")
        cee.set("name",a.name)
        ce.append(cee)
    e.append(ce)
    ce = etree.Element("ret")
    ce.append(self.ret._dumper())
    e.append(ce)
    
    return e

@extend(node.lambda_expr)
def _dumper(self,level=0):
    e = etree.Element("lambda")
    ce = etree.Element("args")
    ce.append(self.args._dumper())
    e.append(ce)
    ce = etree.Element("ret")
    ce.append(self.ret._dumper())
    e.append(ce)
    return e

@extend(node.for_stmt)
def _dumper(self,level=0):
    e = etree.Element("for")
    ce = etree.Element("ident")
    ce.append(self.ident._dumper())
    e.append(ce)
    ce = etree.Element("expr")
    ce.append(self.expr._dumper())
    e.append(ce)
    ce = etree.Element("body")
    ce.append(self.stmt_list._dumper(level+1))
    e.append(ce)
    return e

@extend(node.if_stmt)
def _dumper(self,level=0):
    e = etree.Element("if")
    ce = etree.Element("cond")
    ce.append(self.cond_expr._dumper())
    e.append(ce)
    ce = etree.Element("then")
    ce.append(self.then_stmt._dumper())
    e.append(ce)
    if self.else_stmt:
        ce = etree.Element("else")
        ce.append(self.else_stmt._dumper())
        e.append(ce)        
    return e

@extend(node.while_stmt)
def _dumper(self,level=0):
    e = etree.Element("while")
    ce = etree.Element("cond")
    ce.append(self.cond_expr._dumper())
    e.append(ce)
    ce = etree.Element("body")
    ce.append(self.stmt_list._dumper(level+1))
    e.append(ce)
    return e

@extend(node.try_catch)
def _dumper(self,level=0):
    e = etree.Element("trycatch")
    ce = etree.Element("try")
    ce.append(self.try_stmt._dumper())
    e.append(ce)    
    ce = etree.Element("finally")
    ce.append(self.finally_stmt._dumper())
    e.append(ce)
    return e

@extend(node.builtins)
def _dumper(self,level=0):
    #if not self.ret:
    e = etree.Element("builtins")
    e.set("name",self.__class__.__name__)
    for t in self.args:
        e.append(t._dumper())
    if self.ret is not None:
        ce = etree.Element("ret")
        ce.append(self.ret._dumper())
        e.append(ce)
    return e

    
@extend(node.dot)
def _dumper(self,level=0):
    e = etree.Element("dot")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return e
    
