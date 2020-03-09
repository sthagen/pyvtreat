from abc import ABC

import numpy
import numpy.random

import pandas


class CrossValidationPlan(ABC):
    """Data splitting plan"""

    def __init__(self):
        pass

    def split_plan(self, *, n_rows=None, k_folds=None, data=None, y=None):
        raise NotImplementedError("base class called")

    def __repr__(self):
        return str(type(self))

    def __str__(self):
        return self.__repr__()


class KWayCrossPlanYStratified(CrossValidationPlan):
    """K-way cross validation plan, attempting an even y-distribution"""

    def __init__(self):
        CrossValidationPlan.__init__(self)

    # noinspection PyMethodMayBeStatic
    def _k_way_cross_plan_y_stratified(self, n_rows, k_folds, y=None):
        """randomly split range(n_rows) into k_folds disjoint groups, attempting an even y-distribution"""
        if k_folds < 2:
            k_folds = 2
        n2 = int(numpy.floor(n_rows / 2))
        if k_folds > n2:
            k_folds = n2
        if n_rows <= 2 or k_folds <= 1:
            # degenerate overlap cases
            plan = [
                {"train": [i for i in range(n_rows)], "app": [i for i in range(n_rows)]}
            ]
            return plan
        # first sort by y plus a random key
        if y is None:
            y = numpy.zeros(n_rows)
        d = pandas.DataFrame(
            {
                "y": y,
                "i": [i for i in range(n_rows)],
                "r": numpy.random.uniform(size=n_rows),
            }
        )
        d.sort_values(by=["y", "r"], inplace=True)
        d.reset_index(inplace=True, drop=True)
        # assign y-blocks to lose fine details of y
        fold_size = n_rows / k_folds
        d["block"] = [numpy.floor(i / fold_size) for i in range(n_rows)]
        d.sort_values(by=["block", "r"], inplace=True)
        d.reset_index(inplace=True, drop=True)
        # now assign groups modulo k (ensuring at least one in each group)
        d["grp"] = [i % k_folds for i in range(n_rows)]
        d.sort_values(by=["i"], inplace=True)
        d.reset_index(inplace=True, drop=True)
        grp = numpy.asarray(d["grp"])
        plan = [
            {
                "train": [i for i in range(n_rows) if grp[i] != j],
                "app": [i for i in range(n_rows) if grp[i] == j],
            }
            for j in range(k_folds)
        ]
        return plan

    def split_plan(self, *, n_rows=None, k_folds=None, data=None, y=None):
        if n_rows is None:
            raise ValueError("n_rows must not be None")
        if k_folds is None:
            raise ValueError("k_folds must not be None")
        if y is None:
            raise ValueError("y must not be None")
        return self._k_way_cross_plan_y_stratified(n_rows=n_rows, k_folds=k_folds, y=y)

    def __repr__(self):
        return "vtreat.cross_plan.KWayCrossPlanYStratified()"
