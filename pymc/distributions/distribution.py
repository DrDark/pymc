import theano.tensor as t
import numpy as np
from ..model import Model

__all__ = ['DensityDist', 'Distribution', 'Continuous', 'Discrete']


class Distribution(object):
    """Statistical distribution"""
    def __new__(cls, name, *args, **kwargs):
        try:
            model = Model.get_context()
        except TypeError:
            raise TypeError("No model on context stack, which is needed to use the Normal('x', 0,1) syntax. Add a 'with model:' block")

        if isinstance(name, str):  
            data = kwargs.pop('observed', None)
            dist = cls.dist(*args, **kwargs)
            return model.Var(name, dist, data)
        elif name is None:
            return object.__new__(cls) #for pickle
        else: 
            raise TypeError("needed name or None but got: " + name)

    def __getnewargs__(self):
        return None, 

    @classmethod
    def dist(cls, *args, **kwargs):
        dist = object.__new__(cls)
        dist.__init__(*args, **kwargs)
        return dist

    def __init__(self, shape, dtype, testval=None, defaults=[]):
        self.shape = np.atleast_1d(shape)
        self.dtype = dtype
        self.type = TensorType(self.dtype, self.shape)
        self.testval = testval
        self.defaults = defaults

    def default(self):
        return self.get_test_val(self.testval, self.defaults)

    def get_test_val(self, val, defaults):
        if val is None:
            for v in defaults:
                if hasattr(self, v):
                    val = getattr(self, v)
                    break

        if val is None:
            raise AttributeError(str(self) + " has no default value to use, checked for: " +
                         str(defaults) + " pass testval argument or provide one of these.")

        if isinstance(val, str):
            val = getattr(self, val)

        if isinstance(val, t.TensorVariable):
            return val.tag.test_value

        return val


def TensorType(dtype, shape):
    return t.TensorType(str(dtype), np.atleast_1d(shape) == 1)

class Discrete(Distribution): 
    """Base class for discrete distributions"""
    def __init__(self, shape=(), dtype='int64', *args, **kwargs):
        super(Discrete, self).__init__(shape, dtype, defaults=['mode'], *args, **kwargs)

class Continuous(Distribution): 
    """Base class for continuous distributions"""
    def __init__(self, shape=(), dtype='float64', *args, **kwargs):
        super(Continuous, self).__init__(shape, dtype, defaults=['median', 'mean', 'mode'], *args, **kwargs)

class DensityDist(Distribution):
    """Distribution based on a given log density function."""
    def __init__(self, logp, shape=(), dtype='float64',testval=0, *args, **kwargs):
        super(DensityDist, self).__init__(shape, dtype, testval, *args, **kwargs)
        self.logp = logp
