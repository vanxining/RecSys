#!/usr/bin/env python2

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.optimizers import SGD
from keras.utils import np_utils, generic_utils

import numpy as np


def _to_categorical(y, nb_classes):
    return np_utils.to_categorical(y, nb_classes)


class MLP(Sequential):
    def __init__(self):
        super(MLP, self).__init__()
        self.nb_classes = 0

    def fit(self, X, y):
        input_dim = X.shape[1]

        self.nb_classes = len(np.unique(y))
        assert self.nb_classes == np.max(y) + 1

        y = _to_categorical(y, self.nb_classes)

        # Dense(64) is a fully-connected layer with 64 hidden units.
        # in the first layer, you must specify the expected input data shape:
        # here, 20-dimensional vectors.
        self.add(Dense(64, input_dim=input_dim, init="uniform"))
        self.add(Activation("tanh"))
        self.add(Dropout(0.5))
        self.add(Dense(64, init="uniform"))
        self.add(Activation("tanh"))
        self.add(Dropout(0.5))
        self.add(Dense(self.nb_classes, init="uniform"))
        self.add(Activation("softmax"))

        sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
        self.compile(loss="categorical_crossentropy", optimizer=sgd)

        super(MLP, self).fit(X, y,
                             nb_epoch=20,
                             batch_size=16,
                             show_accuracy=True)

    def predict_proba(self, X):
        return super(MLP, self).predict_proba(X, batch_size=16)
