cimport cython
cimport numpy as np
import numpy as np
import pandas as pd 
from libc.math cimport sqrt, isnan, NAN
from libcpp.deque cimport deque
from scipy.stats import percentileofscore


cdef class Rolling:
    """1-D array rolling"""
    cdef int window
    cdef deque[double] barv
    cdef int na_count
    def __init__(self, int window):
        self.window = window
        self.na_count = window
        cdef int i
        for i in range(window):
            self.barv.push_back(NAN)

    cdef double update(self, double val):
        pass


cdef class Mean(Rolling):
    """1-D array rolling mean"""
    cdef double vsum
    def __init__(self, int window):
        super(Mean, self).__init__(window)
        self.vsum = 0
        
    cdef double update(self, double val):
        self.barv.push_back(val)
        if not isnan(self.barv.front()):
            self.vsum -= self.barv.front()
        else:
            self.na_count -= 1
        self.barv.pop_front()
        if isnan(val):
            self.na_count += 1
            # return NAN
        else:
            self.vsum += val
        return self.vsum / (self.window - self.na_count)


cdef class Slope(Rolling):
    """1-D array rolling slope"""
    cdef double i_sum # can be used as i2_sum
    cdef double x_sum
    cdef double x2_sum
    cdef double y_sum
    cdef double xy_sum
    def __init__(self, int window):
        super(Slope, self).__init__(window)
        self.i_sum  = 0
        self.x_sum  = 0
        self.x2_sum = 0
        self.y_sum  = 0
        self.xy_sum = 0

    cdef double update(self, double val):
        self.barv.push_back(val)
        self.xy_sum = self.xy_sum - self.y_sum
        self.x2_sum = self.x2_sum + self.i_sum - 2*self.x_sum
        self.x_sum = self.x_sum - self.i_sum
        cdef double _val
        _val = self.barv.front()
        if not isnan(_val):
            self.i_sum -= 1
            self.y_sum -= _val
        else:
            self.na_count -= 1
        self.barv.pop_front()
        if isnan(val):
            self.na_count += 1
            # return NAN
        else:
            self.i_sum  += 1
            self.x_sum  += self.window
            self.x2_sum += self.window * self.window
            self.y_sum  += val
            self.xy_sum += self.window * val
        cdef int N = self.window - self.na_count
        return (N*self.xy_sum - self.x_sum*self.y_sum) / \
            (N*self.x2_sum - self.x_sum*self.x_sum)

    
cdef class Resi(Rolling):
    """1-D array rolling residuals"""
    cdef double i_sum # can be used as i2_sum
    cdef double x_sum
    cdef double x2_sum
    cdef double y_sum
    cdef double xy_sum
    def __init__(self, int window):
        super(Resi, self).__init__(window)
        self.i_sum  = 0
        self.x_sum  = 0
        self.x2_sum = 0
        self.y_sum  = 0
        self.xy_sum = 0

    cdef double update(self, double val):
        self.barv.push_back(val)
        self.xy_sum = self.xy_sum - self.y_sum
        self.x2_sum = self.x2_sum + self.i_sum - 2*self.x_sum
        self.x_sum = self.x_sum - self.i_sum
        cdef double _val
        _val = self.barv.front()
        if not isnan(_val):
            self.i_sum -= 1
            self.y_sum -= _val
        else:
            self.na_count -= 1
        self.barv.pop_front()
        if isnan(val):
            self.na_count += 1
            # return NAN
        else:
            self.i_sum  += 1
            self.x_sum  += self.window
            self.x2_sum += self.window * self.window
            self.y_sum  += val
            self.xy_sum += self.window * val
        cdef int N = self.window - self.na_count
        slope = (N*self.xy_sum - self.x_sum*self.y_sum) / \
                (N*self.x2_sum - self.x_sum*self.x_sum)
        x_mean = self.x_sum / N
        y_mean = self.y_sum / N
        interp = y_mean - slope*x_mean
        return val - (slope*self.window + interp)

    
cdef class Rsquare(Rolling):
    """1-D array rolling rsquare"""
    cdef double i_sum
    cdef double x_sum
    cdef double x2_sum
    cdef double y_sum
    cdef double y2_sum
    cdef double xy_sum
    def __init__(self, int window):
        super(Rsquare, self).__init__(window)
        self.i_sum  = 0
        self.x_sum  = 0
        self.x2_sum = 0
        self.y_sum  = 0
        self.y2_sum = 0
        self.xy_sum = 0

    cdef double update(self, double val):
        self.barv.push_back(val)
        self.xy_sum = self.xy_sum - self.y_sum
        self.x2_sum = self.x2_sum + self.i_sum - 2*self.x_sum
        self.x_sum = self.x_sum - self.i_sum
        cdef double _val
        _val = self.barv.front()
        if not isnan(_val):
            self.i_sum  -= 1
            self.y_sum  -= _val
            self.y2_sum -= _val * _val
        else:
            self.na_count -= 1
        self.barv.pop_front()
        if isnan(val):
            self.na_count += 1
            # return NAN
        else:
            self.i_sum  += 1
            self.x_sum  += self.window
            self.x2_sum += self.window * self.window
            self.y_sum  += val
            self.y2_sum += val * val
            self.xy_sum += self.window * val
        cdef int N = self.window - self.na_count
        cdef double rvalue
        rvalue = (N*self.xy_sum - self.x_sum*self.y_sum) / \
            sqrt((N*self.x2_sum - self.x_sum*self.x_sum) * (N*self.y2_sum - self.y_sum*self.y_sum))
        return rvalue * rvalue

    
cdef np.ndarray[double, ndim=1] rolling(Rolling r, np.ndarray a):
    cdef int  i
    cdef int  N = len(a)
    cdef np.ndarray[double, ndim=1] ret = np.empty(N)
    for i in range(N):
        ret[i] = r.update(a[i])
    return ret

def rolling_mean(np.ndarray a, int window):
    cdef Mean r = Mean(window)
    return rolling(r, a)

def rolling_slope(np.ndarray a, int window):
    cdef Slope r = Slope(window)
    return rolling(r, a)

def rolling_rsquare(np.ndarray a, int window):
    cdef Rsquare r = Rsquare(window)
    return rolling(r, a)

def rolling_resi(np.ndarray a, int window):
    cdef Resi r = Resi(window)
    return rolling(r, a)


def rank(x):
    if np.isnan(x[-1]):
        return np.nan
    x1 = x[~np.isnan(x)]
    if x1.shape[0] == 0:
        return np.nan
    return percentileofscore(x1, x1[-1]) / len(x1)
def corr(series1,series2,windows):
    return series1.rolling(windows).corr(series2)




import numpy as np
from scipy import optimize
from scipy import special

class FocalLoss:

    def __init__(self, gamma, alpha=None):
        self.alpha = alpha
        self.gamma = gamma

    def at(self, y):
        if self.alpha is None:
            return np.ones_like(y)
        return np.where(y, self.alpha, 1 - self.alpha)

    def pt(self, y, p):
        p = np.clip(p, 1e-15, 1 - 1e-15)
        return np.where(y, p, 1 - p)

    def __call__(self, y_true, y_pred):
        at = self.at(y_true)
        pt = self.pt(y_true, y_pred)
        return -at * (1 - pt) ** self.gamma * np.log(pt)

    def grad(self, y_true, y_pred):
        y = 2 * y_true - 1  # {0, 1} -> {-1, 1}
        at = self.at(y_true)
        pt = self.pt(y_true, y_pred)
        g = self.gamma
        return at * y * (1 - pt) ** g * (g * pt * np.log(pt) + pt - 1)

    def hess(self, y_true, y_pred):
        y = 2 * y_true - 1  # {0, 1} -> {-1, 1}
        at = self.at(y_true)
        pt = self.pt(y_true, y_pred)
        g = self.gamma

        u = at * y * (1 - pt) ** g
        du = -at * y * g * (1 - pt) ** (g - 1)
        v = g * pt * np.log(pt) + pt - 1
        dv = g * np.log(pt) + g + 1

        return (du * v + u * dv) * y * (pt * (1 - pt))

    def init_score(self, y_true):
        res = optimize.minimize_scalar(
            lambda p: self(y_true, p).sum(),
            bounds=(0, 1),
            method='bounded'
        )
        p = res.x
        log_odds = np.log(p / (1 - p))
        return log_odds

    def lgb_obj(self, preds, train_data):
        y = train_data.get_label()
        p = special.expit(preds)
        return self.grad(y, p), self.hess(y, p)

    def lgb_eval(self, preds, train_data):
        y = train_data.get_label()
        p = special.expit(preds)
        is_higher_better = False
        return 'focal_loss', self(y, p).mean(), is_higher_better
