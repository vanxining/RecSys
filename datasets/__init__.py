import numpy as np


class Dataset(object):
    def __int__(self):
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None


def _normalize(matrix_2d):
    return matrix_2d / matrix_2d.max(axis=0)


def topcoder(normalize):
    dtype = np.float if normalize else np.uint16

    training = np.loadtxt("datasets/training.txt", dtype=dtype)
    test = np.loadtxt("datasets/test.txt", dtype=dtype)

    dataset = Dataset()
    dataset.X_train = training[:, :-1]
    dataset.y_train = training[:, -1]
    dataset.X_test = test[:, :-1]
    dataset.y_test = test[:, -1]

    if normalize:
        dataset.X_train = _normalize(dataset.X_train)
        dataset.X_test = _normalize(dataset.X_test)

    return dataset
