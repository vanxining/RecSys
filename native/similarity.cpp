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

#define ENABLE_CACHE 1

#if ENABLE_CACHE

typedef std::unordered_map<int, PyObject *> Cache;
static std::unordered_map<void *, Cache> gs_cacheMap;

#endif

PyObject *ClearCache(PyObject *);

///////////////////////////////////////////////////////////////////////////////

// TODO: Not thread-safe
// TODO: Cache

static double ALPHA = 0.6;
static double BETA = 0.55;
static double GAMMA = 0.65;

double _SetCoefficient(const char *cef, double val) {
    if (val < 0.0) {
        fprintf(stderr, "New value can't be negative.\n");
        return -1.0;
    }

    double old = 0.0;

    if (strcmp(cef, "alpha") == 0) {
        old = ALPHA;
        ALPHA = val;
    } else if (strcmp(cef, "beta") == 0) {
        old = BETA;
        BETA = val;
    } else if (strcmp(cef, "gamma") == 0) {
        if (val == 0.0) {
            fprintf(stderr, "gamma can't be zero.\n");
            return -1.0;
        }

        old = GAMMA;
        GAMMA = val;
    }

    return old;
}

static PyObject *SetCoefficient(PyObject *self, PyObject *args) {
    const char *cef = nullptr;
    double val = 0;

    if (!PyArg_ParseTuple(args, "sd", &cef, &val)) {
        return nullptr;
    }

    double old = _SetCoefficient(cef, val);
    return PyFloat_FromDouble(old);
}

///////////////////////////////////////////////////////////////////////////////

inline int GetRowCount(PyArrayObject *array) {
    return PyArray_DIM(array, 0);
}

inline int GetColumnCount(PyArrayObject *array) {
    return PyArray_DIM(array, 1);
}

///////////////////////////////////////////////////////////////////////////////

template<typename ET>
class Row {
public:

    Row(PyArrayObject *array, int ri)
        : m_array(array), m_row(ri),
          m_numCols(GetColumnCount(array)),
          m_col(0) {
        
    }

    // Get the internal NumPy array object.
    PyArrayObject *GetArray() const {
        return m_array;
    }

    // Get row index.
    int GetRowIndex() const {
        return m_row;
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

///////////////////////////////////////////////////////////////////////////////

struct RowsNonZeroCache {
    PyArrayObject *m = nullptr;
    std::vector<int16_t> rows;
    int maxCount = 0;
};

static RowsNonZeroCache gs_nzCache;

void CountRowsNonZero(PyArrayObject *m) {
    auto numRows = GetRowCount(m) - 1;

    gs_nzCache.m = m;
    gs_nzCache.rows.clear();
    gs_nzCache.rows.resize(numRows);

    for (auto i = 0; i < numRows; i++) {
        Row<ET> row(m, i);
        auto nz = 0;

        while (row.IsOk()) {
            nz += row.Current();
            row.Next();
        }

        if (gs_nzCache.maxCount < nz) {
            gs_nzCache.maxCount = nz;
        }

        gs_nzCache.rows[i] = nz;
    }
}

///////////////////////////////////////////////////////////////////////////////

PyObject *ClearCache(PyObject *) {
    gs_nzCache.m = nullptr;
    gs_nzCache.rows.clear();
    gs_nzCache.maxCount = 0;

#if ENABLE_CACHE

    for (auto it = gs_cacheMap.begin(); it != gs_cacheMap.end(); ++it) {
        for (auto cit = it->second.begin(); cit != it->second.end(); ++cit) {
            Py_DECREF(cit->second);
        }

        it->second.clear();
    }

    gs_cacheMap.clear();

#endif

    Py_RETURN_NONE;
}

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

#if ENABLE_CACHE

    auto it = gs_cacheMap.find(reinterpret_cast<void *>(func));
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
        Row<ET> yrow(m, i);
        sim.push_back({ i, func(xrow, yrow, nrow) });

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

#if ENABLE_CACHE

    Py_INCREF(ret);
    gs_cacheMap[reinterpret_cast<void *>(func)][userIndex] = ret;

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
        auto co_occurrence = xrow.Current() & yrow.Current();
        if (co_occurrence) {
            similarity += co_occurrence;

            similarity += (yrow.PeekBackward() + yrow.PeekBackward()) * ALPHA;
        }

        xrow.Next();
        yrow.Next();
    }

    return similarity;
}

static PyObject *Neighbor(PyObject *self, PyObject *args) {
    return Calc(self, args, _Neighbor);
}

static double _Neighbor2(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &) {
    double similarity = 0.0;

    while (xrow.IsOk()) {
        auto co_occurrence = xrow.Current() & yrow.Current();
        if (co_occurrence) {
            similarity += co_occurrence;

            similarity += (yrow.PeekBackward(1) + yrow.PeekBackward(1)) * ALPHA;
            similarity += (yrow.PeekBackward(2) + yrow.PeekBackward(2)) * BETA;
        }

        xrow.Next();
        yrow.Next();
    }

    return similarity;
}

static PyObject *Neighbor2(PyObject *self, PyObject *args) {
    return Calc(self, args, _Neighbor2);
}

static double _NeighborGlobal(Row<ET> &xrow, Row<ET> &yrow, Row<ET> &nrow) {
    auto similarity = _Neighbor(xrow, yrow, nrow);

    if (gs_nzCache.m != yrow.GetArray()) {
        CountRowsNonZero(yrow.GetArray());
    }

    double nzCount = gs_nzCache.rows[yrow.GetRowIndex()];
    double maxCount = gs_nzCache.maxCount;

    return similarity * (nzCount / maxCount) * GAMMA;
}

static PyObject *NeighborGlobal(PyObject *self, PyObject *args) {
    return Calc(self, args, _NeighborGlobal);
}

static int _Active(Row<ET> &, Row<ET> &yrow, Row<ET> &) {
    if (gs_nzCache.m != yrow.GetArray()) {
        CountRowsNonZero(yrow.GetArray());
    }

    return gs_nzCache.rows[yrow.GetRowIndex()];
}

static PyObject *Active(PyObject *self, PyObject *args) {
    return Calc(self, args, _Active);
}

static PyMethodDef _Methods[] = {
    { "Naive", Naive, METH_VARARGS, nullptr },
    { "Cosine", Cosine, METH_VARARGS, nullptr },
    { "Breese", Breese, METH_VARARGS, nullptr },
    { "Neighbor", Neighbor, METH_VARARGS, nullptr },
    { "Neighbor2", Neighbor2, METH_VARARGS, nullptr },
    { "NeighborGlobal", NeighborGlobal, METH_VARARGS, nullptr },
    { "Active", Active, METH_VARARGS, nullptr },
    { "ClearCache", (PyCFunction) ClearCache, METH_NOARGS, nullptr },
    { "SetCoefficient", SetCoefficient, METH_VARARGS, nullptr },
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
