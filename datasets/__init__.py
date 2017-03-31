import numpy

import util as util


class Dataset(object):
    def __int__(self):
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None
        self.labels = None


def _normalize(matrix_2d):
    # Collapse the rows (axis=0)
    m = matrix_2d.max(axis=0)

    for i in xrange(m.shape[0]):
        if m[i] <= 1.0:
            m[i] = 1.0

    return matrix_2d / m


def load_dataset(name, normalize):
    dtype = numpy.float if normalize else numpy.uint16

    training = numpy.loadtxt("datasets/training_%s.txt" % name, dtype=dtype)
    test = numpy.loadtxt("datasets/test_%s.txt" % name, dtype=dtype)

    dataset = Dataset()
    dataset.X_train = training[:, :-1]
    dataset.y_train = training[:, -1]
    dataset.X_test = test[:, :-1]
    dataset.y_test = test[:, -1]
    dataset.labels = set(dataset.y_train)

    if normalize:
        dataset.X_train = _normalize(dataset.X_train)
        dataset.X_test = _normalize(dataset.X_test)

    return dataset


def generate_developer_mappings(dataset_name, mappings):
    with open("datasets/dev_mappings_%s.py" % dataset_name, "w") as outf:
        outf.write("developers = (\n")

        rmappings = [0] * len(mappings)
        for dev, label in mappings.iteritems():
            rmappings[label] = dev

        fmt = "    %s,\n" % ("%d" if type(rmappings[0]) is int else '"%s"')
        for label in rmappings:
            outf.write(fmt % label)

        outf.write(")\n")
