#include <Python.h>
#include <numpy/arrayobject.h>

#include <vector>
#include <unordered_map>
#include <algorithm>

///////////////////////////////////////////////////////////////////////////////

typedef npy_uint8 ET;

template<typename T>
struct Similarity {
    int peer_index;
    T value;
};

template<typename T>
bool operator < (const Similarity<T> &s1, const Similarity<T> &s2) {
    return s1.value < s2.value;
}

///////////////////////////////////////////////////////////////////////////////

#define USE_CACHE

#ifdef USE_CACHE

typedef std::unordered_map<int, PyObject *> Cache;
static std::unordered_map<void *, Cache> gs_cacheMap;

PyObject *ClearCache(PyObject *) {
    for (auto it = gs_cacheMap.begin(); it != gs_cacheMap.end(); ++it) {
        for (auto cit = it->second.begin(); cit != it->second.end(); ++cit) {
            Py_DECREF(cit->second);
        }
    }

    Py_RETURN_NONE;
}
#endif

///////////////////////////////////////////////////////////////////////////////

inline int GetRowCount(PyArrayObject *array) {
    return PyArray_DIM(array, 0);
}

inline int GetColumnCount(PyArrayObject *array) {
    return PyArray_DIM(array, 1);
}

template<typename ET>
class Row {
public:

    Row(PyArrayObject *array, int ri)
        : m_array(array), m_row(ri),
          m_numCols(GetColumnCount(array)),
          m_col(0) {
        
    }

    // Get current element value.
    ET Current() const {
        return const_cast<Row<ET> *>(this)->Current();
    }

    // Get current (writable) element.
    ET &Current() {
        return GetItem(m_col);
    }

    bool IsOk() {
        return m_col < m_numCols;
    }

    void Next() {
        m_col++;
    }

    void Reset() {
        m_col = 0;
    }

    // Return the value right before the current one.
    ET PeekBackward(int n = 1) {
        if (m_col < n) {
            return 0;
        }

        return GetItem(m_col - n);
    }

    // Return the value right after the current one.
    ET PeekForward(int n = 1) {
        if (m_col >= m_numCols - n) {
            return 0;
        }

        return GetItem(m_col + n);
    }

private:

    ET &GetItem(int col) {
        ET *p = (ET *) PyArray_GETPTR2(m_array, m_row, col);
        return *p;
    }

    PyArrayObject *m_array;
    const int m_row;
    const int m_numCols;
    int m_col;
};

template <typename Functor>
static PyObject *Calc(PyObject *self, PyObject *args, Functor func) {
    PyArrayObject *m = nullptr;
    auto userIndex = -1;
    auto topN = 0;

    if (!PyArg_ParseTuple(args, "O!ii", &PyArray_Type, &m, &userIndex, &topN)) {
        return nullptr;
    }

    if (topN <= 0) {
        PyErr_SetString(PyExc_ValueError, "topN should be positive!");
        return nullptr;
    }

#ifdef USE_CACHE

    auto it = gs_cacheMap.find(func);
    if (it != gs_cacheMap.end()) {
        auto cit = it->second.find(userIndex);
        if (cit != it->second.end()) {
            Py_INCREF(cit->second);
            return cit->second;
        }
    }

#endif

    // The last row is the "nrow". (The number of registrants.)
    auto numRows = GetRowCount(m) - 1;
    Row<ET> nrow(m, numRows);
    Row<ET> xrow(m, userIndex);

    typedef decltype(func(xrow, xrow, xrow)) SimValT;
    std::vector<Similarity<SimValT>> sim;
    sim.reserve(numRows);

    for (auto i = 0; i < numRows; i++) {
        sim.push_back({ i, func(xrow, Row<ET>(m ,i), nrow) });

        nrow.Reset();
        xrow.Reset();
    }

    // Not similar to itself.
    sim[userIndex].value = 0;

    //----------------------------

    std::make_heap(sim.begin(), sim.end());

    PyObject *ret = PyTuple_New(topN);
    auto i = 0;

    for (; i < topN && !sim.empty(); i++) {
        std::pop_heap(sim.begin(), sim.end());

        const auto &curr = sim.back();
        if (curr.value == 0) {
            break;
        }

        PyTuple_SET_ITEM(ret, i, PyInt_FromSsize_t(curr.peer_index));

        sim.pop_back();
    }

    if (i < topN) {
        _PyTuple_Resize(&ret, i);
    }

#ifdef USE_CACHE

    Py_INCREF(ret);
    gs_cacheMap[func][userIndex] = ret;

#endif

    return ret;
}

static int _Naive(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &) {
    auto similarity = 0;

    while (xrow.IsOk()) {
        similarity += xrow.Current() & yrow.Current();

        xrow.Next();
        yrow.Next();
    }

    return similarity;
}

static PyObject *Naive(PyObject *self, PyObject *args) {
    return Calc(self, args, _Naive);
}

static double _Cosine(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &) {
    double iproduct = 0.0;
    double x2 = 0.0;
    double y2 = 0.0;

    while (xrow.IsOk()) {
        ET xv = xrow.Current();
        ET yv = yrow.Current();

        iproduct += xv * yv;
        x2 += xv * xv;
        y2 += yv * yv;

        xrow.Next();
        yrow.Next();
    }

    return iproduct / sqrt(x2 * y2);
}

static PyObject *Cosine(PyObject *self, PyObject *args) {
    return Calc(self, args, _Cosine);
}

static double _Breese(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &nrow) {
    double inverse = 0.0;
    auto x2 = 0;
    auto y2 = 0;

    while (xrow.IsOk()) {
        ET xv = xrow.Current();
        ET yv = yrow.Current();

        assert(nrow.Current() > 0);

        if (xv == yv && xv == 1) {
            inverse += 1 / log(1 + nrow.Current());
        }

        x2 += xv;
        y2 += yv;

        xrow.Next();
        yrow.Next();
        nrow.Next();
    }

    return inverse / sqrt(x2 * y2);
}

static PyObject *Breese(PyObject *self, PyObject *args) {
    return Calc(self, args, _Breese);
}

static double _Neighbor(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &) {
    double similarity = 0.0;

    while (xrow.IsOk()) {
        similarity += xrow.Current() & yrow.Current();
        similarity += (xrow.PeekBackward() & yrow.PeekBackward()) * 0.5;
        similarity += (xrow.PeekForward() & yrow.PeekForward()) * 0.5;

        xrow.Next();
        yrow.Next();
    }

    return similarity;
}

static PyObject *Neighbor(PyObject *self, PyObject *args) {
    return Calc(self, args, _Neighbor);
}

static PyMethodDef _Methods[] = {
    { "Naive", Naive, METH_VARARGS, nullptr },
    { "Cosine", Cosine, METH_VARARGS, nullptr },
    { "Breese", Breese, METH_VARARGS, nullptr },
    { "Neighbor", Neighbor, METH_VARARGS, nullptr },
    { "ClearCache", (PyCFunction) ClearCache, METH_NOARGS, nullptr },
    {  nullptr, nullptr, 0, nullptr }
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
   "sim",
    nullptr,
   -1,
   _Methods,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

PyMODINIT_FUNC PyInit_sim(void) {
    PyObject *m = PyModule_Create(&moduledef);

    if (!m) {
        return nullptr;
    }
    else {
        import_array();
    }

    return m;
}

#else
    
PyMODINIT_FUNC initsim(void) {
    PyObject *m = Py_InitModule("sim", _Methods);

    if (!m) {
        return;
    }
    else {
        import_array();
    }
}

#endif
