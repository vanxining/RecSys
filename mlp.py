#!/usr/bin/env python2

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.optimizers import SGD
from keras.utils import np_utils, generic_utils

import numpy as np


training = np.loadtxt("datasets/training.txt", dtype=np.uint16)
test = np.loadtxt("datasets/test.txt", dtype=np.uint16)

X_train = training[:, :-1]
y_train = training[:, -1]

X_test = test[:, :-1]
y_test = test[:, -1]

input_dim = X_train.shape[1]
nb_classes = len(np.unique(y_train))
assert nb_classes == np.max(y_train) + 1

y_train, y_test = [np_utils.to_categorical(x, nb_classes) for x in (y_train, y_test)]

model = Sequential()

# Dense(64) is a fully-connected layer with 64 hidden units.
# in the first layer, you must specify the expected input data shape:
# here, 20-dimensional vectors.
model.add(Dense(64, input_dim=input_dim, init="uniform"))
model.add(Activation("tanh"))
model.add(Dropout(0.5))
model.add(Dense(64, init="uniform"))
model.add(Activation("tanh"))
model.add(Dropout(0.5))
model.add(Dense(nb_classes, init="uniform"))
model.add(Activation("softmax"))

sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss="categorical_crossentropy", optimizer=sgd)

model.fit(X_train, y_train,
          nb_epoch=20,
          batch_size=16,
          show_accuracy=True)

score = model.evaluate(X_test, y_test, batch_size=16)
print score
