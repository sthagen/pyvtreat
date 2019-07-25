# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 11:40:41 2019

@author: johnmount
"""


import pandas
import numpy


import vtreat.vtreat_impl as vtreat_impl
import vtreat.util

# had been getting Future warnings on seemining correct (no missing values) use of
# Pandas indexing from vtreat.vtreat_impl.cross_patch_refit_y_aware_cols
#
# /Users/johnmount/anaconda3/envs/aiAcademy/lib/python3.7/site-packages/pandas/core/series.py:942: FutureWarning:
# Passing list-likes to .loc or [] with any missing label will raise
# KeyError in the future, you can use .reindex() as an alternative.
#
# See the documentation here:
# https://pandas.pydata.org/pandas-docs/stable/indexing.html#deprecate-loc-reindex-listlike
#  return self.loc[key]
# /Users/johnmount/anaconda3/envs/aiAcademy/lib/python3.7/site-packages/pandas/core/indexing.py:1494: FutureWarning:
# Passing list-likes to .loc or [] with any missing label will raise
# KeyError in the future, you can use .reindex() as an alternative.
#
# See the documentation here:
# https://pandas.pydata.org/pandas-docs/stable/indexing.html#deprecate-loc-reindex-listlike
#  return self._getitem_tuple(key)
#
# working around with:
# https://stackoverflow.com/questions/15777951/how-to-suppress-pandas-future-warning
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

def vtreat_parameters(user_params=None):
    """build a vtreat parmaters dictionary, adding in user choices"""
    params = {'use_hierarchical_estimate':True,
              'coders':{'clean_copy',
                        'missing_indicator',
                        'indicator_code',
                        'impact_code',
                        'deviance_code',
                        'logit_code',
                        'prevalence_code'},
              }.copy()
    if user_params is not None:
        pkeys = set(params.keys())
        for k in user_params.keys():
            if k not in pkeys:
                raise Exception("paramatere key " + str(k) + " not recognized")
            params[k] = user_params[k]
    return params


class NumericOutcomeTreatment:
    """manage a treatment plan for a numeric outcome (regression)"""

    def __init__(self, *, var_list=None, outcome_name=None, cols_to_copy=None, params=None):
        if params is None:
            params = vtreat_parameters()
        if var_list is None:
            var_list = []
        if cols_to_copy is None:
            cols_to_copy = []
        if outcome_name not in set(cols_to_copy):
            cols_to_copy = cols_to_copy + [outcome_name]
        self.var_list_ = var_list.copy()
        self.outcome_name_ = outcome_name
        self.cols_to_copy_ = cols_to_copy.copy()
        self.params_ = params.copy()
        self.plan_ = None
        self.score_frame_ = None
        self.cross_plan_ = None

    def fit(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        self.fit_transform(X=X, y=y)
        return self

    def transform(self, X):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        return vtreat_impl.perform_transform(x=X, plan=self.plan_)

    def fit_transform(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        y = numpy.asarray(y, dtype=numpy.float64)
        if numpy.isnan(y).sum() > 0:
            raise Exception("y should not have any missing/NA/NaN values")
        # model for independent transforms
        self.plan_ = None
        self.score_frame_ = None
        self.plan_ = vtreat_impl.fit_numeric_outcome_treatment(
            X=X,
            y=y,
            var_list=self.var_list_,
            outcome_name=self.outcome_name_,
            cols_to_copy=self.cols_to_copy_,
            params=self.params_
        )
        res = self.transform(X)
        # patch in cross-frame versions of complex columns such as impact
        self.cross_plan_ = vtreat.util.k_way_cross_plan(n_rows=X.shape[0], k_folds=5)
        cross_frame = vtreat_impl.cross_patch_refit_y_aware_cols(
            x=X, y=y, res=res, plan=self.plan_, cross_plan=self.cross_plan_
        )
        # use cross_frame to compute variable effects
        self.score_frame_ = vtreat_impl.score_plan_variables(
            cross_frame=cross_frame, outcome=y, plan=self.plan_
        )
        return cross_frame


class BinomialOutcomeTreatment:
    """manage a treatment plan for a target outcome (binomial classification)"""

    def __init__(
        self, *, var_list=None, outcome_name=None, outcome_target, cols_to_copy=None, params=None
    ):
        if params is None:
            params = vtreat_parameters()
        if cols_to_copy is None:
            cols_to_copy = []
        if var_list is None:
            var_list = []
        if outcome_name not in set(cols_to_copy):
            cols_to_copy = cols_to_copy + [outcome_name]
        self.var_list_ = var_list.copy()
        self.outcome_name_ = outcome_name
        self.outcome_target_ = outcome_target
        self.cols_to_copy_ = cols_to_copy.copy()
        self.params_ = params.copy()
        self.plan_ = None
        self.score_frame_ = None
        self.cross_plan_ = None

    def fit(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        self.fit_transform(X=X, y=y)
        return self

    def transform(self, X):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        return vtreat_impl.perform_transform(x=X, plan=self.plan_)

    def fit_transform(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        if numpy.isnan(y).sum() > 0:
            raise Exception("y should not have any missing/NA/NaN values")
        # model for independent transforms
        self.plan_ = None
        self.score_frame_ = None
        self.plan_ = vtreat_impl.fit_binomial_outcome_treatment(
            X=X,
            y=y,
            outcome_target=self.outcome_target_,
            var_list=self.var_list_,
            outcome_name=self.outcome_name_,
            cols_to_copy=self.cols_to_copy_,
            params=self.params_
        )
        res = self.transform(X)
        # patch in cross-frame versions of complex columns such as impact
        self.cross_plan_ = vtreat.util.k_way_cross_plan(n_rows=X.shape[0], k_folds=5)
        cross_frame = vtreat_impl.cross_patch_refit_y_aware_cols(
            x=X, y=y, res=res, plan=self.plan_, cross_plan=self.cross_plan_
        )
        # use cross_frame to compute variable effects
        self.score_frame_ = vtreat_impl.score_plan_variables(
            cross_frame=cross_frame,
            outcome=numpy.asarray(numpy.asarray(y) == self.outcome_target_, dtype=numpy.float64),
            plan=self.plan_
        )
        return cross_frame


class MultinomialOutcomeTreatment:
    """manage a treatment plan for a set of outcomes (multinomial classification)"""

    def __init__(self, *, var_list=None, outcome_name=None, cols_to_copy=None, params=None):
        if var_list is None:
            var_list = []
        if cols_to_copy is None:
            cols_to_copy = []
        if params is None:
            params = vtreat_parameters()
        if outcome_name not in set(cols_to_copy):
            cols_to_copy = cols_to_copy + [outcome_name]
        self.var_list_ = var_list.copy()
        self.outcome_name_ = outcome_name
        self.outcomes_ = None
        self.cols_to_copy_ = cols_to_copy.copy()
        self.params_ = params.copy()
        self.plan_ = None
        self.score_frame_ = None
        self.cross_plan_ = None

    def fit(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        self.fit_transform(X=X, y=y)
        return self

    def transform(self, X):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        return vtreat_impl.perform_transform(x=X, plan=self.plan_)

    def fit_transform(self, X, y):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is None:
            y = X[self.outcome_name_]
        if not X.shape[0] == len(y):
            raise Exception("X.shape[0] should equal len(y)")
        if numpy.isnan(y).sum() > 0:
            raise Exception("y should not have any missing/NA/NaN values")
        # model for independent transforms
        self.plan_ = None
        self.score_frame_ = None
        self.outcomes_ = numpy.unique(y)
        self.plan_ = vtreat_impl.fit_multinomial_outcome_treatment(
            X=X,
            y=y,
            var_list=self.var_list_,
            outcome_name=self.outcome_name_,
            cols_to_copy=self.cols_to_copy_,
            params=self.params_
        )
        res = self.transform(X)
        # patch in cross-frame versions of complex columns such as impact
        self.cross_plan_ = vtreat.util.k_way_cross_plan(n_rows=X.shape[0], k_folds=5)
        cross_frame = vtreat_impl.cross_patch_refit_y_aware_cols(
            x=X, y=y, res=res, plan=self.plan_, cross_plan=self.cross_plan_
        )
        # use cross_frame to compute variable effects

        def si(oi):
            sf = vtreat_impl.score_plan_variables(
                cross_frame=cross_frame,
                outcome=numpy.asarray(numpy.asarray(y) == oi, dtype=numpy.float64),
                plan=self.plan_)
            sf["outcome_target"] = oi
            return sf
        score_frames = [si(oi) for oi in self.outcomes_]
        self.score_frame_ = pandas.concat(score_frames, axis=0)
        self.score_frame_.reset_index(inplace=True, drop=True)
        return cross_frame


class UnsupervisedTreatment:
    """manage an unsupervised treatment plan"""

    def __init__(self, *, var_list=None, outcome_name=None, cols_to_copy=None, params=None):
        if var_list is None:
            var_list = []
        if cols_to_copy is None:
            cols_to_copy = []
        if params is None:
            params = vtreat_parameters()
        if outcome_name not in set(cols_to_copy):
            cols_to_copy = cols_to_copy + [outcome_name]
        self.var_list_ = var_list.copy()
        self.outcome_name_ = outcome_name
        self.cols_to_copy_ = cols_to_copy.copy()
        self.params_ = params.copy()
        self.plan_ = None

    def fit(self, X, y=None):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        if y is not None:
            raise Exception("y should be None")
        # model for independent transforms
        self.plan_ = None
        self.plan_ = vtreat_impl.fit_unsupervised_treatment(
            X=X,
            var_list=self.var_list_,
            outcome_name=self.outcome_name_,
            cols_to_copy=self.cols_to_copy_,
            params = self.params_
        )
        return self

    def transform(self, X):
        if not isinstance(X, pandas.DataFrame):
            raise Exception("X should be a Pandas DataFrame")
        return vtreat_impl.perform_transform(x=X, plan=self.plan_)

    def fit_transform(self, X, y=None):
        if y is not None:
            raise Exception("y should be None")
        self.fit(X=X)
        return self.transform(X)
