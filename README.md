# ModernPlot

A GNUplot-inspired interactive scientific data plotting and curve fitting application built with PyQt6 and Matplotlib.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)


## Overview

ModernPlot is a desktop application for quickly loading, visualizing, and fitting scientific data files. It combines the flexibility of GNUplot-style data exploration with a modern graphical interface. The plot canvas uses a white background with publication-quality styling so that exported figures are paper-ready with no post-processing.

### Key Features

- **Universal file loading** - CSV, TSV, whitespace-delimited `.dat`/`.txt` files, with automatic delimiter and header detection (including `#`-prefixed comment headers from CLASS, CAMB, Cobaya, etc.)
- **C++ accelerated loader** - optional pybind11 extension parses files directly into NumPy arrays at ~3× the speed of pure Python; auto-detected at startup
- **Streaming fallback** - if the C++ extension isn't built, large files load in a background thread with a progress bar and cancel button; the UI never freezes
- **Multi-series plotting** - checkbox-based column selection lets you overlay multiple Y columns on one plot
- **5 plot types** - Line, Scatter, Line + Scatter, Step, Bar
- **Axis scaling** - independent Linear / Log / Symlog for each axis
- **8 curve fitting models** - Linear, Polynomial (degree 2–15), Exponential, Power Law, Logarithmic, Gaussian, Sinusoidal, and Custom Expression
- **7 fit scale transforms** - linear, log₁₀-log₁₀, ln-ln, semilog-x (log₁₀ or ln), semilog-y (log₁₀ or ln)
- **Fit diagnostics** - parameter values ± uncertainties, R², reduced χ², RMS residual, degrees of freedom, optional residuals subplot with ±1σ band
- **Paper-ready exports** - white-background plots exported as PNG (200 DPI), PDF, or SVG
- **Dark UI** - Tokyo Night theme for the application chrome; white canvas for the plot

---

## Installation ( Recommended )

### Pip Install
```bash
pip install modernplot
```
- All the required dependencies are out of the box.
- Uses FastLoader for loading files, falls back to native Python (for Windows)

## Manual Installation 

### Requirements

- Python 3.10 or later
- A C++ compiler (g++, clang++)
- Linux, macOS, or Windows(C++ backend is not supported as of now)

### Install dependencies

```bash
pip install PyQt6 matplotlib numpy scipy pybind11
```

### Build the C++ fast loader (recommended)

```bash
make
```

This compiles `fast_loader.cpp` into a Python extension (`.so`) using pybind11. The app auto-detects it at startup — if present, file loading is ~3× faster. If not built, the app falls back to a pure Python streaming loader.

**Makefile targets:**

| Target | Description |
|--------|-------------|
| `make` | Build `fast_loader.so` |
| `make check` | Build and verify the import works |
| `make clean` | Remove compiled `.so` files |

**Manual build** (if `make` isn't available):

```bash
c++ -O3 -shared -fPIC $(python3 -m pybind11 --includes) \
    fast_loader.cpp -o fast_loader$(python3-config --extension-suffix)
```

### Run

```bash
python modernplot.py
```

The file label shows `[C++]` when the fast loader is active.

### Optional: Build standalone binary

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ModernPlot modernplot.py
```

The binary will be in `dist/ModernPlot`.

---

## Quick Start

1. Launch the application: `python modernplot.py`
2. Click **Open File…** or use the toolbar button
3. Select your data file (`.csv`, `.tsv`, `.dat`, `.txt`, `.asc`)
4. The file loads with a progress bar; columns appear as checkboxes in the left panel
5. Select the **X axis** column from the dropdown
6. **Check** one or more Y columns to plot
7. Click **Plot**
8. To fit: choose a fit type, select the target Y column in "Fit Y", and click **Plot + Fit**
9. Export via **Export** button (PNG / PDF / SVG)

---

## User Interface

The application is split into two regions:

### Left Panel (Controls)

A scrollable panel containing all configuration options, organized into collapsible groups:

#### Data Source
- **Open File…** - opens a file dialog for supported formats
- **Progress bar** - appears during loading; shows row count and estimated total
- **Cancel** - stops a long-running load
- **Data preview table** - shows the first 50 rows of loaded data

#### Columns
- **X axis** - dropdown to select the X column (includes a "(row index)" option for index-based plotting)
- **Y axis** - checkboxes for each column; check multiple to overlay series on one plot

#### Plot Options
- **Type** - Line, Scatter, Line + Scatter, Step, Bar
- **X scale / Y scale** - linear, log, symlog (applied independently)
- **Show grid** - toggle dashed grid lines
- **Show legend** - toggle the legend box

#### Curve Fitting
- **Fit type** - dropdown with 9 options (see [Fit Models](#fit-models))
- **Degree** - polynomial degree spinner (visible only when Polynomial is selected, range 2–15)
- **f(x) =** - custom expression input (visible only when Custom Expression is selected)
- **Fit Y** - which Y column to fit (defaults to first checked column)
- **Show residuals subplot** - adds a residuals panel below the main plot
- **Show equation on plot** - overlays the fit equation and R² on the canvas
- **Show confidence band** - shades ±1σ around the fit curve
- **Fit scale** - data transform applied before fitting (see [Fit Scales](#fit-scales))

#### Labels
- **Title** - plot title (optional)
- **X label / Y label** - axis labels (default to column names if empty)

#### Buttons
- **Plot** - plot data only (no fit)
- **Plot + Fit** - plot data and overlay the fit curve
- **Export** - save figure as PNG (200 DPI) / PDF / SVG
- **Clear** - reset the canvas

#### Fit Results
- Displays fit equation, parameter table (value ± error), R², reduced χ², RMS residual, N, and degrees of freedom
- **Copy Results** - copies the plain-text results to clipboard

### Right Panel (Canvas)

- **Matplotlib navigation toolbar** - zoom, pan, home, save (built-in matplotlib tools)
- **Plot canvas** - white background, black text, publication-quality styling

---

## Supported File Formats

ModernPlot auto-detects file structure based on extension and content:

| Extension | Parsing method | Delimiter |
|-----------|---------------|-----------|
| `.csv`    | Python `csv.reader` | comma |
| `.tsv`    | Python `csv.reader` | tab |
| `.dat`, `.txt`, `.asc`, others | Whitespace splitting | any whitespace |

### Header detection

Headers are detected in three ways (in priority order):

1. **`#`-prefixed comment header** - the last `#` line before data begins is parsed as column names. Supports multi-line comment blocks (e.g., CLASS output with several comment lines followed by `# 1:l  2:TT  3:EE ...`). Works with comma, tab, or whitespace separation within the header line.

2. **Non-numeric first row** - if the first data row contains any non-numeric value, it is treated as a header row.

3. **Auto-generated** - if no header is detected, columns are named `col_0`, `col_1`, etc.

### Compatibility

Tested with output from:
- **CLASS** - `*_cl.dat`, `*_pk.dat` (multi-line `#` comments, `1:l  2:TT` style headers)
- **Cobaya/MontePython** - MCMC chain files (whitespace-padded, `#`-header with long column names like `chi2__planck_2018_lowl.TT`)
- **NumPy `savetxt`** - with or without `# header` lines
- **Generic CSV/TSV** - Excel exports, pandas `.to_csv()`, etc.
- **Fortran-style** - fixed-width whitespace-delimited with `!` or `#` comment headers

---

## Fit Models

All fits use `scipy.optimize.curve_fit` (Levenberg-Marquardt) with automatic initial parameter guessing.

### Built-in models

| Model | Equation | Parameters | Initial guess strategy |
|-------|----------|------------|----------------------|
| **Linear** | `y = a·x + b` | a (slope), b (intercept) | Least squares |
| **Polynomial** | `y = aₙxⁿ + ... + a₁x + a₀` | aₙ…a₀ (degree 2–15) | `numpy.polyfit` |
| **Exponential** | `y = a·exp(b·x) + c` | a (amplitude), b (rate), c (offset) | Range-based |
| **Power Law** | `y = a·x^b + c` | a (coefficient), b (exponent), c (offset) | Requires x > 0 |
| **Logarithmic** | `y = a·ln(x) + b` | a (coefficient), b (offset) | Requires x > 0 |
| **Gaussian** | `y = a·exp(-(x-μ)²/2σ²) + c` | a (amplitude), μ (center), σ (width), c (offset) | Peak detection |
| **Sine** | `y = a·sin(b·x + c) + d` | a (amplitude), b (frequency), c (phase), d (offset) | FFT frequency estimate |

### Custom expressions

Select "Custom Expression" and enter any formula using:

- **Variable:** `x`
- **Fit parameters:** `a`, `b`, `c`, `d`, `e` (up to 5; only those present in the expression are fitted)
- **Functions:** `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `log2`, `sqrt`, `abs`, `sinh`, `cosh`, `tanh`, `arcsin`, `arccos`, `arctan`, `power`
- **Constants:** `pi`, `e`

**Examples:**
```
a*x**2 + b*sin(c*x)
a*exp(-b*x)*cos(c*x + d)
a*log(x)**2 + b*log(x) + c
a*tanh(b*(x - c)) + d
```

Parameters are auto-detected from the expression using regex boundary matching, so `exp` won't be confused with parameter `e`, and `abs` won't match parameter `a`.

---

## Fit Scales

The fit scale dropdown transforms data before fitting. This is essential when your data spans many orders of magnitude or when the X column is already in log space.

| Scale | X transform | Y transform | Use case |
|-------|------------|------------|----------|
| **linear** | none | none | Default; raw data fitting |
| **log₁₀-log₁₀** | log₁₀(x) | log₁₀(y) | Power law fitting over decades |
| **ln-ln** | ln(x) | ln(y) | Same, with natural log |
| **semilog-x log₁₀(X)** | log₁₀(x) | none | Logarithmic relationships |
| **semilog-x ln(X)** | ln(x) | none | Same, natural log |
| **semilog-y log₁₀(Y)** | none | log₁₀(y) | Exponential decay/growth |
| **semilog-y ln(Y)** | none | ln(y) | **Use this when X is already ln(k)** |

### Important: when X is already in log space

If your data file has X = ln(k) (common for primordial power spectrum outputs), do **not** use log-log — that would take log(log(k)). Instead:

1. Set fit scale to **semilog-y ln(Y)**
2. Choose **Linear** fit type
3. The slope gives `d ln(P)/d ln(k)` directly
4. The spectral index is `nₛ = 1 + slope`

### How fit scale works

When a non-linear fit scale is selected:

- Data is transformed before fitting (log₁₀ or ln applied to the chosen axes)
- Non-positive values are automatically filtered out
- The fit is performed entirely in transformed space
- Data points and fit curve are plotted in transformed coordinates
- Axis labels update to show the transform (e.g., "ln(P_s)")
- R², residuals, and all statistics are computed in the transformed space

---

## Fit Results

After fitting, the results panel shows:

- **Fit type** and **fit scale** (if non-linear)
- **Equation** with numerical parameter values substituted
- **Transform note** (e.g., "x → ln(x), y → ln(y)")
- **Parameter table** - each parameter with value ± 1σ uncertainty (from covariance matrix diagonal)
- **R²** - coefficient of determination (color-coded: green > 0.95, orange > 0.8, red otherwise)
- **χ²_red** - reduced chi-squared (assuming unit weights)
- **RMS** - root mean square of residuals
- **N** - number of data points used
- **DoF** - degrees of freedom (N − number of parameters)

The **Copy Results** button copies the plain-text version to clipboard for pasting into papers or notebooks.

---

## Performance

ModernPlot is designed to handle large datasets without freezing. It uses a two-tier loading strategy:

### C++ fast loader (primary)

When the `fast_loader` extension is compiled (via `make`), files are parsed entirely in C++ using `strtod` and returned as a zero-copy NumPy array via pybind11. There is no Python string intermediate — the file goes directly from disk to a `float64` array. The app shows a loading screen on the canvas during this time.

### Python streaming loader (fallback)

If the C++ extension isn't available, files are read in a background `QThread` in chunks of 5,000 rows. After loading, string data is converted to a NumPy array in a chunked loop with UI progress updates. This is slower but requires no compilation.

### Instant column access

Regardless of loader, column access is a single NumPy slice (`self.np_data[:, idx]`), taking ~6ms for 500K rows.

### Automatic downsampling

When plotting, datasets larger than 15,000 points per series are automatically downsampled using stride-based decimation. This keeps matplotlib rendering fast without losing the visual shape of the data. Curve fitting always uses the full dataset.



---

## Architecture

### File structure

```
modernplot/
├── modernplot.py            # Main application (~1700 lines)
├── fast_loader.cpp          # C++ accelerated file parser (pybind11)
├── Makefile                 # Build system for the C++ extension
├── build_fast_loader.py     # Alternative Python build script
├── README.md
└── LICENSE
```

### Key classes

| Class | Language | Purpose |
|-------|----------|---------|
| `ModernPlot(QMainWindow)` | Python | Main application window; UI, plotting, fitting |
| `DataLoaderWorker(QThread)` | Python | Background streaming file loader (fallback) |
| `fast_loader` (pybind11 module) | C++ | High-performance file parser, returns NumPy arrays |

### Key functions

| Function | Purpose |
|----------|---------|
| `load_data(filepath)` | Synchronous file loader (used internally by tests) |
| `_extract_comment_header(filepath)` | Parses `#`-prefixed header lines |
| `_parse_whitespace_delimited(filepath, header)` | Whitespace-delimited file parser |
| `perform_fit(x, y, fit_type, ...)` | Executes curve fitting; returns fit curve, parameters, equation |
| `compute_r_squared(y_data, y_fit)` | R² (coefficient of determination) |
| `compute_chi_squared_red(y_data, y_fit, n_params)` | Reduced chi-squared |
| `apply_mpl_dark_style()` | Sets matplotlib rcParams for white-background paper style |

### Signal flow (data loading)

**C++ path (when `fast_loader.so` is present):**
```
User clicks "Open File" → file dialog → path selected
  → Loading screen drawn on canvas (filename, file size)
  → QTimer.singleShot(50ms) defers load so screen paints
  → _open_file_cpp(): calls fast_loader.load(path)
      → C++ reads file, parses floats, returns NumPy array (zero-copy)
  → Table preview + column selectors populated
  → Summary screen shown on canvas
```

**Python fallback path (when `fast_loader.so` is absent):**
```
User clicks "Open File" → file dialog → path selected
  → Loading screen drawn on canvas
  → DataLoaderWorker(QThread) started
  → Worker emits headers_ready → column selectors populated
  → Worker emits chunk_ready every 5000 rows → raw_data grows
  → Worker emits progress → progress bar updates
  → Worker emits finished → NumPy conversion → string data freed
```

### Theming

The application uses a dual-theme approach:

- **UI chrome** - Tokyo Night dark theme via Qt stylesheet (`DARK_BG`, `DARK_SURFACE`, `DARK_BORDER`, etc.)
- **Plot canvas** - white background with dark text via matplotlib rcParams (`WHITE`, `BLACK`)
- **Plot colors** - matplotlib tab10 palette, chosen for good contrast on white paper

This means the dark sidebar is comfortable for extended use, while exported plots are immediately publication-ready.

---

## Configuration Constants

These constants at the top of `modernplot.py` can be adjusted:

| Constant | Default | Purpose |
|----------|---------|---------|
| `CHUNK_SIZE` | 5000 | Rows per streaming chunk |
| `MAX_PLOT_POINTS` | 15000 | Downsampling threshold per series |
| `PLOT_COLORS` | tab10 palette | Colors for data series |
| `FIT_COLOR` | `#ff7f0e` | Color of the fit curve |
| `FIT_COLOR2` | `#d62728` | Color of residuals |

---

## Dependencies

| Package | Version | Required | Purpose |
|---------|---------|----------|---------|
| `PyQt6` | ≥ 6.5 | Yes | GUI framework |
| `matplotlib` | ≥ 3.7 | Yes | Plotting |
| `numpy` | ≥ 1.24 | Yes | Numeric arrays |
| `scipy` | ≥ 1.10 | Yes | Curve fitting (`scipy.optimize.curve_fit`) |
| `pybind11` | ≥ 2.11 | No (build only) | Compiling the C++ fast loader |
| C++ compiler | g++ or clang++ | No | Compiling the C++ fast loader |

---


## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

When modifying the fitting engine, run the built-in smoke test:

```python
python -c "
import numpy as np
from modernplot import perform_fit
x = np.linspace(0.1, 10, 200)
for ft in ['Linear  (a·x + b)', 'Polynomial', 'Exponential  (a·exp(b·x) + c)',
           'Power Law  (a·x^b + c)', 'Logarithmic  (a·ln(x) + b)',
           'Gaussian  (a·exp(-(x-μ)²/2σ²) + c)', 'Sine  (a·sin(b·x + c) + d)',
           'Custom Expression']:
    y = 2.5*x**1.3 + np.random.normal(0, 0.1, len(x))
    kwargs = {}
    if ft.startswith('Poly'): kwargs['poly_degree'] = 3
    if ft.startswith('Custom'): kwargs['custom_expr'] = 'a*x**b + c'
    try:
        res = perform_fit(x, y, ft, **kwargs)
        print(f'  ✓ {ft.split(chr(40))[0].strip()}')
    except Exception as e:
        print(f'  ✗ {ft.split(chr(40))[0].strip()}: {e}')
"
```
