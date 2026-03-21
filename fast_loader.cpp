/*
 * fast_loader.cpp — High-performance scientific data file parser
 *
 * Parses CSV / TSV / whitespace-delimited files directly into NumPy float64 arrays.
 * Handles # comment headers (CLASS, CAMB, Cobaya, Fortran output).
 * Returns (headers: list[str], data: numpy.ndarray[float64, shape=(N, M)])
 *
 * Build:
 *   c++ -O3 -shared -fPIC $(python3 -m pybind11 --includes) fast_loader.cpp \
 *       -o fast_loader$(python3-config --extension-suffix)
 *
 * Usage from Python:
 *   import fast_loader
 *   headers, data = fast_loader.load("file.dat")
 *   # headers: list of strings
 *   # data: numpy float64 array, shape (nrows, ncols)
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <cctype>

namespace py = pybind11;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

static inline std::string trim(const std::string &s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    size_t end = s.find_last_not_of(" \t\r\n");
    return s.substr(start, end - start + 1);
}

static inline bool is_numeric(const std::string &s) {
    if (s.empty()) return false;
    char *end = nullptr;
    std::strtod(s.c_str(), &end);
    // If end points to the end of the string (or only whitespace), it's numeric
    while (*end && std::isspace(*end)) ++end;
    return *end == '\0';
}

// Split a string by whitespace
static std::vector<std::string> split_whitespace(const std::string &line) {
    std::vector<std::string> tokens;
    std::istringstream iss(line);
    std::string tok;
    while (iss >> tok) {
        tokens.push_back(tok);
    }
    return tokens;
}

// Split by a specific delimiter (comma or tab)
static std::vector<std::string> split_delim(const std::string &line, char delim) {
    std::vector<std::string> tokens;
    std::istringstream iss(line);
    std::string tok;
    while (std::getline(iss, tok, delim)) {
        tokens.push_back(trim(tok));
    }
    return tokens;
}

// Detect file extension
static std::string get_ext(const std::string &filepath) {
    size_t dot = filepath.rfind('.');
    if (dot == std::string::npos) return "";
    std::string ext = filepath.substr(dot);
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return ext;
}

// ---------------------------------------------------------------------------
// Header extraction — find the last # comment line before data
// ---------------------------------------------------------------------------

struct HeaderInfo {
    std::vector<std::string> names;
    bool found = false;
};

static HeaderInfo extract_comment_header(const std::string &filepath) {
    HeaderInfo info;
    std::ifstream f(filepath);
    if (!f.is_open()) return info;

    std::string last_comment;
    std::string line;

    while (std::getline(f, line)) {
        std::string trimmed = trim(line);
        if (trimmed.empty()) continue;
        if (trimmed[0] == '#' || trimmed[0] == '!') {
            last_comment = trimmed;
        } else {
            break;  // first data line
        }
    }

    if (last_comment.empty()) return info;

    // Strip leading # or ! characters
    size_t start = last_comment.find_first_not_of("#! \t");
    if (start == std::string::npos) return info;
    std::string header_text = last_comment.substr(start);

    // Split by comma, tab, or whitespace
    std::vector<std::string> names;
    if (header_text.find(',') != std::string::npos) {
        names = split_delim(header_text, ',');
    } else if (header_text.find('\t') != std::string::npos) {
        names = split_delim(header_text, '\t');
    } else {
        names = split_whitespace(header_text);
    }

    // Sanity check: at least one token should be non-numeric
    bool has_non_numeric = false;
    for (const auto &n : names) {
        if (!is_numeric(n)) { has_non_numeric = true; break; }
    }

    if (has_non_numeric && !names.empty()) {
        info.names = names;
        info.found = true;
    }
    return info;
}

// ---------------------------------------------------------------------------
// Main loader
// ---------------------------------------------------------------------------

static std::pair<std::vector<std::string>, py::array_t<double>>
load_file(const std::string &filepath) {
    std::string ext = get_ext(filepath);

    // Determine delimiter mode
    enum Mode { WHITESPACE, COMMA, TAB };
    Mode mode = WHITESPACE;
    if (ext == ".csv") mode = COMMA;
    else if (ext == ".tsv") mode = TAB;

    // Extract comment header
    HeaderInfo hdr = extract_comment_header(filepath);

    // Open file
    std::ifstream f(filepath);
    if (!f.is_open()) {
        throw std::runtime_error("Cannot open file: " + filepath);
    }

    // Parse all data rows into a flat double vector
    std::vector<std::string> headers;
    std::vector<double> flat_data;
    size_t ncols = 0;
    size_t nrows = 0;
    bool headers_set = false;

    std::string line;
    while (std::getline(f, line)) {
        std::string trimmed = trim(line);
        if (trimmed.empty()) continue;
        if (trimmed[0] == '#' || trimmed[0] == '!') continue;

        // Split the line
        std::vector<std::string> fields;
        if (mode == COMMA) {
            fields = split_delim(trimmed, ',');
        } else if (mode == TAB) {
            fields = split_delim(trimmed, '\t');
        } else {
            fields = split_whitespace(trimmed);
        }

        if (fields.empty()) continue;

        // First data row: determine headers and column count
        if (!headers_set) {
            if (hdr.found) {
                headers = hdr.names;
                ncols = fields.size();
                // Pad or trim header to match data width
                while (headers.size() < ncols) {
                    headers.push_back("col_" + std::to_string(headers.size()));
                }
                if (headers.size() > ncols) {
                    headers.resize(ncols);
                }
            } else {
                // Check if first row is a header (any non-numeric field)
                bool is_header_row = false;
                for (const auto &fld : fields) {
                    if (!is_numeric(fld)) { is_header_row = true; break; }
                }

                if (is_header_row) {
                    headers = fields;
                    ncols = fields.size();
                    headers_set = true;
                    continue;  // skip this row as data
                } else {
                    ncols = fields.size();
                    for (size_t i = 0; i < ncols; ++i) {
                        headers.push_back("col_" + std::to_string(i));
                    }
                }
            }
            headers_set = true;
        }

        // Parse fields to doubles
        for (size_t i = 0; i < ncols; ++i) {
            if (i < fields.size()) {
                char *end = nullptr;
                double val = std::strtod(fields[i].c_str(), &end);
                // Check if conversion consumed the whole string
                while (*end && std::isspace(*end)) ++end;
                if (*end != '\0') {
                    flat_data.push_back(std::nan(""));
                } else {
                    flat_data.push_back(val);
                }
            } else {
                flat_data.push_back(std::nan(""));
            }
        }
        ++nrows;
    }

    if (nrows == 0) {
        throw std::runtime_error("No data rows found in file: " + filepath);
    }

    // Create NumPy array — zero-copy from our vector
    // We need to move the data into a capsule so Python owns it
    auto *data_ptr = new std::vector<double>(std::move(flat_data));
    py::capsule capsule(data_ptr, [](void *p) {
        delete reinterpret_cast<std::vector<double>*>(p);
    });

    py::array_t<double> arr(
        {static_cast<py::ssize_t>(nrows), static_cast<py::ssize_t>(ncols)},  // shape
        {static_cast<py::ssize_t>(ncols * sizeof(double)),                    // row stride
         static_cast<py::ssize_t>(sizeof(double))},                          // col stride
        data_ptr->data(),                                                     // data pointer
        capsule                                                               // prevent dealloc
    );

    return {headers, arr};
}

// ---------------------------------------------------------------------------
// Python module
// ---------------------------------------------------------------------------

PYBIND11_MODULE(fast_loader, m) {
    m.doc() = "High-performance scientific data file parser. "
              "Parses CSV/TSV/whitespace-delimited files directly into NumPy arrays.";

    m.def("load", &load_file,
          py::arg("filepath"),
          R"doc(
Load a data file and return (headers, data).

Parameters
----------
filepath : str
    Path to the data file (.csv, .tsv, .dat, .txt, .asc, etc.)

Returns
-------
tuple of (list[str], numpy.ndarray)
    headers: column names (auto-detected from # comments, first row, or generated)
    data: float64 array of shape (nrows, ncols), NaN for unparseable values

Supports:
    - CSV (comma-delimited)
    - TSV (tab-delimited)
    - Whitespace-delimited (.dat, .txt, .asc, etc.)
    - # and ! prefixed comment headers (CLASS, CAMB, Cobaya, Fortran)
    - Auto-detection of header vs data rows
)doc");
}
