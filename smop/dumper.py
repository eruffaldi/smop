# smop -- Simple Matlab to Python compiler
# Copyright 2014 Emanuele Ruffaldi @ PERCRO Scuola Superiore Sant'Anna 

import logging
logger = logging.getLogger(__name__)
import node,options
from node import extend
from lxml import etree

def dumper(t,*args):
    return t._dumper(*args)

def addtype(e,self):
    if hasattr(self,"_xtype"):
        e.set("type",str(getattr(self,"_xtype")))
    return e

@extend(node)
def _dumper(self,*args):
    e = etree.Element("dumper_notimplemented")
    e.set("class",self.__class__.__name__)
    return addtype(e,self)

@extend(node.matrix)
def _dumper(self,level=0):
    e = etree.Element("matrix")
    for t in self.args:
        e.append(t._dumper())
    return addtype(e,self)

@extend(node.cellarrayref)
def _dumper(self,level=0):
    e = etree.Element("cellarrayref")
    e.append(self.func_expr._dumper())
    e.append(self.args._dumper())
    return addtype(e,self)

@extend(node.cellarray)
def _dumper(self,level=0):
    e = etree.Element("cellarray")
    e.append(self.args._dumper())
    return addtype(e,self)

@extend(node.ravel)
def _dumper(self,level=0):
    e = etree.Element("ravel")
    e.append(self.args[0]._dumper())
    return addtype(e,self)

@extend(node.transpose)
def _dumper(self,level=0):
    e = etree.Element("transpose")
    e.append(self.args[0]._dumper())
    return addtype(e,self)

@extend(node.expr_stmt)
def _dumper(self,level=0):
    return self.expr._dumper()

@extend(node.return_stmt)
def _dumper(self,level=0):
    e = etree.Element("return")
    if self.ret:
        e.append(self.ret._dumper())
    return addtype(e,self)

@extend(node.continue_stmt)
def _dumper(self,level=0):
    return etree.Element("continue")

@extend(node.global_stmt)
def _dumper(self,level=0):
    e = etree.Element("global")
    for t in self.global_list:
        e.append(t._dumper())
    return addtype(e,self)

@extend(node.global_list)
def _dumper(self,level=0):
    e = etree.Element("global_list")
    for t in self:
        e.append(t._dumper())
    return addtype(e,self)

@extend(node.break_stmt)
def _dumper(self,level=0):
    return etree.Element("break")

@extend(node.string)
def _dumper(self,level=0):
    e = etree.Element("string")
    e.set("value",str(self.value))
    return addtype(e,self)

@extend(node.number)
def _dumper(self,level=0):
    e = etree.Element("number")
    e.set("value",str(self.value))
    return addtype(e,self)

@extend(node.logical)
def _dumper(self,level=0):
    e = etree.Element("logical")
    e.set("value",str(self.value))
    return addtype(e,self)
    
@extend(node.add)
def _dumper(self,level=0):
    e = etree.Element("add")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return addtype(e,self)

@extend(node.sub)
def _dumper(self,level=0):
    e = etree.Element("sub")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return addtype(e,self)

@extend(node.expr)
def _dumper(self,level=0):
    e = etree.Element("expr_op")
    e.set("op",self.op)
    for t in self.args:
        e.append(t._dumper())
    return addtype(e,self)


@extend(node.arrayref)
def _dumper(self,level=0):
    e = etree.Element("arrayref")
    e.append(self.func_expr._dumper())
    e.append(self.args._dumper())
    return addtype(e,self)
    

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
    return addtype(e,self)

@extend(node.let)
def _dumper(self,level=0):
    e = etree.Element("let")
    ce = etree.Element("target")
    ce.append(self.ret._dumper(level+1))
    e.append(ce)
    ce = etree.Element("value")
    ce.append(self.args._dumper())
    e.append(ce)
    return addtype(e,self)

@extend(node.expr_list)
def _dumper(self,level=0):
    e = etree.Element("expr_list")
    for t in self:
        e.append(t._dumper())
    return addtype(e,self)

@extend(node.concat_list)
def _dumper(self,level=0):
    e = etree.Element("concat_list")
    for t in self:
        e.append(t._dumper())
    return addtype(e,self)

@extend(node.function)
def _dumper(self,level=0):
    e = etree.Element("function")
    ce = etree.Element("head")
    ce.append(self.head._dumper(level))
    e.append(ce)
    ce = etree.Element("body")
    ce.append(self.body._dumper(level+1))
    e.append(ce)
    return addtype(e,self)
        
@extend(node.ident)
def _dumper(self,level=0):
    e = etree.Element("ident")
    e.set("name",self.name)
    return addtype(e,self)

@extend(node.stmt_list)
def _dumper(self,level=0):
    e = etree.Element("stmt_list")
    for t in self:
        e.append(t._dumper(level))
    return addtype(e,self)

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
    return addtype(e,self)

@extend(node.lambda_expr)
def _dumper(self,level=0):
    e = etree.Element("lambda")
    ce = etree.Element("args")
    ce.append(self.args._dumper())
    e.append(ce)
    ce = etree.Element("ret")
    ce.append(self.ret._dumper())
    e.append(ce)
    return addtype(e,self)

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
    return addtype(e,self)

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
    return addtype(e,self)

@extend(node.while_stmt)
def _dumper(self,level=0):
    e = etree.Element("while")
    ce = etree.Element("cond")
    ce.append(self.cond_expr._dumper())
    e.append(ce)
    ce = etree.Element("body")
    ce.append(self.stmt_list._dumper(level+1))
    e.append(ce)
    return addtype(e,self)

@extend(node.try_catch)
def _dumper(self,level=0):
    e = etree.Element("trycatch")
    ce = etree.Element("try")
    ce.append(self.try_stmt._dumper())
    e.append(ce)    
    ce = etree.Element("finally")
    ce.append(self.finally_stmt._dumper())
    e.append(ce)
    return addtype(e,self)

@extend(node.builtins)
def _dumper(self,level=0):
    e = etree.Element("builtins")
    e.set("name",self.__class__.__name__)
    for t in self.args:
        e.append(t._dumper())
    if self.ret is not None:
        ce = etree.Element("ret")
        ce.append(self.ret._dumper())
        e.append(ce)
    return addtype(e,self)

    
@extend(node.dot)
def _dumper(self,level=0):
    e = etree.Element("dot")
    e.append(self.args[0]._dumper())
    e.append(self.args[1]._dumper())
    return addtype(e,self)
    
