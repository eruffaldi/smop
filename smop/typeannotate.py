# smop -- Simple Matlab to Python compiler
# Copyright 2014 Emanuele Ruffaldi @ PERCRO Scuola Superiore Sant'Anna 
#
#
# Ideas: special function calls for typecasting
# Ideas: constant marker during typeannotation
# Ideas: scope management for local variables + external info for arguments and global (how specified?)
# Ideas: special external functions with known behaviors (e.g. fft) 

import logging
logger = logging.getLogger(__name__)
import node,options
from node import extend
import math


class TypeSpec:
    def __init__(self,name=None,sizes=None,iscomplex=False):
        self.name = name
        self.sizes = sizes
        self.iscomplex = iscomplex
    def __ne__(self,other):
        return not self.__eq__(other)
    def __eq__(self,other):
        # something None means different
        if self.name is None or other.name is None or self.sizes is None or other.sizes is None:
            return False
        if self.name != other.name:
            return False
        if len(self.sizes) != len(other.sizes):
            return False
        if self.sizes != other.sizes:
            return False
        return self.iscomplex == other.iscomplex
    def __str__(self):
        if self.sizes is None:
            if self.name is None:
                return "unknown"
            elif self.name == "void":
                return "void"
            ss = ""
        else:
            ss = ",".join([str(x) for x in self.sizes])
        return "%s[%s]%s" % (self.name is None and "unknown" or self.name, ss, self.iscomplex and "complex" or "") 

tunk = TypeSpec()
tscalar = TypeSpec("double",[1])
tlogical = TypeSpec("logical",[1])
tvoid = TypeSpec("void")

def annotate(t,*args):
    return t._annotate(*args)

@extend(node)
def _annotate(self,*args):
    #logger.error("Unimplemented %s",self.__class__.__name__)
    setattr(self,"_xtype",tunk)

@extend(node.matrix)
def _annotate(self,level=0):
    base = None
    for t in self.args:
        t._annotate()
        if base is None:
            base = t._xtype.name
        elif base != t._xtype.name:
            base = "unknown"
    if len(self.args) == 1 and self.args[0].__class__ == node.concat_list:
        self._xtype = self.args[0]._xtype
        return
    else:
        rows = len(self.args)
    if rows > 0:
        cols = len(self.args[0])
    else:
        cols = 0
    setattr(self,"_xtype",TypeSpec(base,[rows,cols]))

@extend(node.cellarrayref)
def _annotate(self,level=0):
    self.func_expr._annotate()
    self.args._annotate()
    #logger.error("Unimplemented %s",self.__class__.__name__)
    setattr(self,"_xtype",tunk)

@extend(node.cellarray)
def _annotate(self,level=0):
    for t in self.args:
        t._annotate()
    rows = len(self.args)
    if rows > 0:
        cols = len(self.args[0])
    else:
        cols = 0
    setattr(self,"_xtype",TypeSpec("cell",[rows,cols]))

@extend(node.ravel)
def _annotate(self,level=0):
    self.args[0]._annotate()
    #logger.error("Unimplemented %s",self.__class__.__name__)
    setattr(self,"_xtype",tunk)

@extend(node.transpose)
def _annotate(self,level=0):
    self.args[0]._annotate()
    t = getattr(self.args[0],"_xtype")
    if t.sizes is not None:
        if len(t.sizes) > 2:
            logging.error("Unsupported transpose on multidim")
        elif len(t.sizes) == 2:
            t = TypeSpec(t.name,(t.sizes[1],t.sizes[0],))
        setattr(self,"_xtype",t)
    else:
        setattr(self,"_xtype",tunk)

@extend(node.expr_stmt)
def _annotate(self,level=0):
    self.expr._annotate()

@extend(node.return_stmt)
def _annotate(self,level=0):
    if self.ret:
        self.ret._annotate()

@extend(node.continue_stmt)
def _annotate(self,level=0):
    pass

@extend(node.global_stmt)
def _annotate(self,level=0):
    pass

@extend(node.global_list)
def _annotate(self,level=0):
    pass

@extend(node.break_stmt)
def _annotate(self,level=0):
    pass

@extend(node.string)
def _annotate(self,level=0):
    setattr(self,"_xtype",TypeSpec("char",[1,len(self.value)]))

@extend(node.number)
def _annotate(self,level=0):
    setattr(self,"_xtype",tscalar)

@extend(node.logical)
def _annotate(self,level=0):
    setattr(slef,"_xtype",tlogical)
    
@extend(node.add)
def _annotate(self,level=0):
    setattr(self,"_xtype",tunk)

@extend(node.sub)
def _annotate(self,level=0):
    setattr(self,"_xtype",tunk)

@extend(node.expr)
def _annotate(self,level=0):
    for t in self.args:
        t._annotate()
    self._xtype = tunk
    if self.op == "-":
        self._xtype = self.args[0]._xtype
    elif self.op == "parens":
        if len(self.args) == 1:
            self._xtype = self.args[0]._xtype

    elif self.op == ":":
        if len(self.args) == 2:
            if self.args[0].__class__ == node.number and self.args[1].__class__ == node.number:
                first = self.args[0].value
                last = self.args[1].value
                k = last-first+1
            else:
                return
        elif len(self.args) == 3:
            if self.args[0].__class__ == node.number and self.args[1].__class__ == node.number and self.args[2].__class__ == node.number:
                first = self.args[0].value
                last  = self.args[1].value
                step = self.args[2].value
                if step < 0 and last > first:
                    k = 0
                elif step > 0 and last < first:
                    k = 0
                elif step == 0:
                    k = 0
                else:   
                    k = int(math.floor((last-first)/step))+1
            else:
                return
        else:
            return
        self._xtype = TypeSpec("double",[1,k]) #actually virtual indices




@extend(node.arrayref)
def _annotate(self,level=0):
    self.func_expr._annotate()
    self.args._annotate()
    setattr(self,"_xtype",tunk)
    

@extend(node.funcall)
def _annotate(self,level=0):
    self.func_expr._annotate()
    self.args._annotate()
    setattr(self,"_xtype",tunk)

@extend(node.let)
def _annotate(self,level=0):
    self.ret._annotate(level+1)
    self.args._annotate()
    if self.ret.__class__ is node.ident:
        self.ret._xtype = self.args._xtype
    self._xtype = tvoid

@extend(node.expr_list)
def _annotate(self,level=0):
    base = None
    baseunk = False
    for t in self:
        t._annotate()
        if not baseunk:
            if base is None:
                base = t._xtype
            elif base != t._xtype:
                baseunk = True
    if base is not None and not baseunk:
        if base.name == "void":
            self._xtype = tvoid
        else:
            self._xtype = TypeSpec(base.name,[1,len(self)],False)
    else:
        self._xtype = tunk

@extend(node.concat_list)
def _annotate(self,level=0):
    base = None
    for t in self:
        t._annotate()
        if base is None:
            base = t._xtype
        elif base != t._xtype:
            base = "unknown"
    if base is not None and base is not "unknown" and len(base.sizes) == 2:
        self._xtype = TypeSpec(base.name,[len(self),base.sizes[1]],False)
    else:
        self._xtype = tunk

@extend(node.function)
def _annotate(self,level=0):
    self.head._annotate(level)
    self.body._annotate(level+1)
        
@extend(node.ident)
def _annotate(self,level=0):
    setattr(self,"_xtype",tunk)

@extend(node.stmt_list)
def _annotate(self,level=0):
    for t in self:
        t._annotate(level)

@extend(node.func_decl)
def _annotate(self,level=0):
    pass

@extend(node.lambda_expr)
def _annotate(self,level=0):
    self.args._annotate()
    self.ret._annotate()

@extend(node.for_stmt)
def _annotate(self,level=0):
    self.ident._annotate()
    self.expr._annotate()
    self.stmt_list._annotate(level+1)

@extend(node.if_stmt)
def _annotate(self,level=0):
    self.cond_expr._annotate()
    self.then_stmt._annotate()
    if self.else_stmt:
        self.else_stmt._annotate()

@extend(node.while_stmt)
def _annotate(self,level=0):
    self.cond_expr._annotate()
    self.stmt_list._annotate(level+1)

@extend(node.try_catch)
def _annotate(self,level=0):
    self.try_stmt._annotate()
    self.finally_stmt._annotate()

@extend(node.builtins)
def _annotate(self,level=0):
    for t in self.args:
        t._annotate()
    if self.ret is not None:
        self.ret._annotate()
    
@extend(node.dot)
def _annotate(self,level=0):
    self.args[0]._annotate()
    self.args[1]._annotate()
    return e
    
