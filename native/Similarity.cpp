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

PyObject *clear_cache(PyObject *) {
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
        : m_array(array), m_row(ri), m_col(0) {
        
    }

    // Get current element value.
    ET Current() const {
        return const_cast<Row<ET> *>(this)->Current();
    }

    // Get current (writable) element.
    ET &Current() {
        ET *p = (ET *) PyArray_GETPTR2(m_array, m_row, m_col);
        return *p;
    }

    bool IsOk() {
        return m_col < GetColumnCount(m_array);
    }

    void Next() {
        m_col++;
    }

    void Reset() {
        m_col = 0;
    }

private:

    PyArrayObject *m_array;
    const int m_row;
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

    auto numRows = GetRowCount(m);
    Row<ET> xrow(m, userIndex);

    typedef decltype(func(xrow, xrow)) SimValT;
    std::vector<Similarity<SimValT>> sim;
    sim.reserve(numRows);

    for (auto i = 0; i < numRows; i++) {
        sim.push_back({ i, func(xrow, Row<ET>(m ,i)) });
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

static int _Naive(Row<ET> &xrow, Row<ET> &yrow) {
    auto difference = 0;

    while (xrow.IsOk()) {
        difference += xrow.Current() & yrow.Current();

        xrow.Next();
        yrow.Next();
    }

    return difference;
}

static PyObject *naive(PyObject *self, PyObject *args) {
    return Calc(self, args, _Naive);
}

static double _Cosine(Row<ET> &xrow, Row<ET> &yrow) {
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

static PyObject *cosine(PyObject *self, PyObject *args) {
    return Calc(self, args, _Cosine);
}

static PyMethodDef _Methods[] = {
    { "naive", naive, METH_VARARGS, nullptr },
    { "cosine", cosine, METH_VARARGS, nullptr },
    { "clear_cache", (PyCFunction) clear_cache, METH_NOARGS, nullptr },
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
