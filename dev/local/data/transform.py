#AUTOGENERATED! DO NOT EDIT! File to edit: dev/02_transforms.ipynb (unless otherwise specified).

__all__ = ['anno_ret', 'cmp_instance', 'ShowTitle', 'Int', 'Float', 'Str', 'load_image', 'PILBase', 'PILImage',
           'PILMask', 'TensorBase', 'TensorImage', 'TensorMask', 'TypeDispatch', 'TfmMeta', 'Transform',
           'TupleTransform', 'ItemTransform']

from ..imports import *
from ..test import *
from ..core import *
from ..notebook.showdoc import show_doc

from types import MethodType

def anno_ret(func):
    "Get the return annotation of `func`"
    ann = typing.get_type_hints(func)
    if not ann: return None
    typ = ann.get('return')
    return list(typ.__args__) if getattr(typ, '_name', '')=='Tuple' else typ

cmp_instance = functools.cmp_to_key(lambda a,b: 0 if a==b else 1 if issubclass(a,b) else -1)

def _p1_anno(f):
    "Get the annotation of first param of `f`"
    ann = [o for n,o in typing.get_type_hints(f).items() if n!='return']
    return ann[0] if ann else object

class ShowTitle:
    "Base class that adds a simple `show`"
    def show(self, ctx=None, **kwargs): return show_title(str(self), ctx=ctx)

class Int(int, ShowTitle): pass
class Float(float, ShowTitle): pass
class Str(str, ShowTitle): pass
add_docs(Int, "An `int` with `show`"); add_docs(Str, "An `str` with `show`"); add_docs(Float, "An `float` with `show`")

def load_image(fn, *args, **kwargs):
    im = PIL.Image.open(fn, *args, **kwargs)
    im.load()
    return im._new(im.im)

class PILBase(PIL.Image.Image):
    _show_args = {'cmap':'viridis'}
    def __new__(cls, x, *args, **kwargs):
        if not isinstance(x,PIL.Image.Image): return super().__new__(cls)
        x.__class__ = cls
        return x

    def __init__(self, x=None):
        if not isinstance(x,PIL.Image.Image): return super().__init__()

    @classmethod
    def open(cls, fn, *args, **kwargs): return cls(load_image(fn, *args, **kwargs))

    def show(self, ctx=None, **kwargs): return show_image(self, ctx=ctx, **{**self._show_args, **kwargs})

class PILImage(PILBase): pass

class PILMask(PILBase):
    _show_args = {'alpha':0.5, 'cmap':'tab20'}

class TensorBase(Tensor):
    _show_args = {'cmap':'viridis'}

    def __new__(cls, x, *args, **kwargs):
        if not isinstance(x,Tensor): return super().__new__(cls)
        x.__class__ = cls
        return x

    def __init__(self, *args, **kwargs):
        if not (args and isinstance(args[0],Tensor)): return super().__init__(*args, **kwargs)

    def show(self, ctx=None, **kwargs): return show_image(self, ctx=ctx, **{**self._show_args, **kwargs})

class TensorImage(TensorBase): pass

class TensorMask(TensorBase):
    _show_args = {'alpha':0.5, 'cmap':'tab20'}

class TypeDispatch:
    "Dictionary-like object; `__getitem__` matches keys of types using `issubclass`"
    def __init__(self, *funcs):
        self.funcs,self.cache = {},{}
        for f in funcs: self.add(f)

    def _reset(self):
        self.funcs = {k:self.funcs[k] for k in sorted(self.funcs, key=cmp_instance, reverse=True)}
        self.cache = {**self.funcs}

    def add(self, f):
        "Add type `t` and function `f`"
        self.funcs[_p1_anno(f) or object] = f
        self._reset()

    def __repr__(self): return str({getattr(k,'__name__',str(k)):v.__name__ for k,v in self.funcs.items()})
    def __getitem__(self, k):
        "Find first matching type that is a super-class of `k`"
        if k in self.cache: return self.cache[k]
        types = [f for f in self.funcs if issubclass(k,f)]
        res = self.funcs[types[0]] if types else None
        self.cache[k] = res
        return res

class TfmMeta(type):
    def __new__(cls, name, bases, dct):
        res = super().__new__(cls, name, bases, dct)
        res.fs = (TypeDispatch(),TypeDispatch())
        if hasattr(res,'encodes'): res.fs[True ].add(res.encodes)
        if hasattr(res,'decodes'): res.fs[False].add(res.decodes)
        return res

    def __call__(cls, *args, **kwargs):
        f = args[0] if args else None
        if isinstance(f,Callable) and f.__name__ in ('decode','encode','_'):
            d = cls.fs[f.__name__ != 'decode']
            d.add(f)
            return f
        return super().__call__(*args, **kwargs)

class Transform(metaclass=TfmMeta):
    "Delegates (`__call__`,`decode`) to (`encodes`,`decodes`) if `filt` matches"
    filt,init_enc,as_item_force,as_item = None,False,None,True
    def __init__(self, enc=None, dec=None, filt=None, as_item=True):
        self.filt,self.as_item = ifnone(filt, self.filt),as_item
        self.init_enc = enc or dec
        if not self.init_enc: return
        self.fs = (TypeDispatch(),TypeDispatch())
        if enc: self.fs[True] .add(enc)
        if dec: self.fs[False].add(dec)

    @property
    def use_as_item(self): return ifnone(self.as_item_force, self.as_item)
    def __call__(self, x, **kwargs): return self.call(True,  x, **kwargs)
    def decode  (self, x, **kwargs): return self.call(False, x, **kwargs)
    def __repr__(self): return f'{self.use_as_item} {self.fs}'

    def call(self, is_enc, x, filt=None, **kwargs):
        if filt!=self.filt and self.filt is not None: return x
        f = self.func(is_enc, x)
        if self.use_as_item: return self._do_call(f, x, **kwargs)
        return tuple(self._do_call(f_, x_, **kwargs) for f_,x_ in zip(f,x))

    def lookup(self, is_enc, x):
        f = self.fs[is_enc][type(x)]
        return (f or noop) if self.init_enc else MethodType(f or noops, self)

    def func(self, is_enc, x, filt=None):
        if self.use_as_item: return self.lookup(is_enc,x)
        return [self.lookup(is_enc,x_) for x_ in x]

    def _do_call(self, f, x, **kwargs):
        if f is None: return x
        res = f(x, **kwargs)
        typ_r = ifnone(anno_ret(f), type(x))
        return typ_r(res) if typ_r!=NoneType and not isinstance(res, typ_r) else res

class TupleTransform(Transform):
    "`Transform` that always treats `as_item` as `False`"
    as_item_force=False

class ItemTransform (Transform):
    "`Transform` that always treats `as_item` as `True`"
    as_item_force=True