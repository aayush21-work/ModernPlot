#!/usr/bin/env python3
"""
ModernPlot — A GNUplot-inspired interactive plotting tool built with PyQt6 + Matplotlib.

Features:
  • Open CSV / TSV / whitespace-delimited data files
  • Preview data in a table
  • Choose X and Y columns (multiple Y supported)
  • Scatter or Line plot modes
  • Log / Linear scale for each axis independently
  • Curve fitting: linear, polynomial, exponential, power, log, Gaussian, sine, custom
  • Fit results panel with parameters, R², equation, residuals plot
  • Axis labels, title, grid toggle
  • Export plot as PNG / PDF / SVG
  • Dark scientific aesthetic
"""

import sys
import os
import csv
import re
import traceback
import numpy as np
from scipy.optimize import curve_fit

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QLineEdit, QGroupBox, QSplitter, QMessageBox, QListWidget,
    QAbstractItemView, QStatusBar, QFrame, QSizePolicy, QToolBar,
    QSpinBox, QTextEdit, QScrollArea, QProgressBar,
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib

# Optional: C++ accelerated file loader (pybind11)
try:
    import fast_loader as _fast_loader
    HAS_FAST_LOADER = True
except ImportError:
    HAS_FAST_LOADER = False


# ---------------------------------------------------------------------------
# Dark palette — Tokyo Night
# ---------------------------------------------------------------------------
DARK_BG      = "#1a1b26"
DARK_SURFACE = "#24283b"
DARK_BORDER  = "#414868"
ACCENT       = "#7aa2f7"
ACCENT2      = "#bb9af7"
TEXT_PRIMARY  = "#c0caf5"
TEXT_DIM      = "#565f89"
GREEN         = "#9ece6a"
RED           = "#f7768e"
ORANGE        = "#e0af68"
CYAN          = "#7dcfff"
WHITE         = "#FFFFFF"
BLACK         = "#343434"

# Plot colors chosen for good contrast on white background
PLOT_COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#17becf", "#e377c2", "#8c564b"]
FIT_COLOR   = "#ff7f0e"
FIT_COLOR2  = "#d62728"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", monospace;
    font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {DARK_BORDER};
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: {ACCENT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
QPushButton {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {DARK_BORDER};
    border-color: {ACCENT};
}}
QPushButton#plotBtn {{
    background-color: {ACCENT};
    color: {DARK_BG};
    border: none;
    font-size: 14px;
    padding: 8px 24px;
}}
QPushButton#plotBtn:hover {{
    background-color: #89b4fa;
}}
QPushButton#fitBtn {{
    background-color: {ORANGE};
    color: {DARK_BG};
    border: none;
    font-size: 13px;
    padding: 7px 20px;
}}
QPushButton#fitBtn:hover {{
    background-color: #f0c078;
}}
QPushButton#exportBtn {{
    background-color: {GREEN};
    color: {DARK_BG};
    border: none;
}}
QPushButton#exportBtn:hover {{
    background-color: #b5e8a0;
}}
QComboBox {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 100px;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    selection-background-color: {DARK_BORDER};
    border: 1px solid {DARK_BORDER};
}}
QComboBox::drop-down {{
    border: none;
}}
QLineEdit {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QListWidget {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 2px;
}}
QListWidget::item:selected {{
    background-color: {DARK_BORDER};
    color: {ACCENT};
}}
QListWidget::item:hover {{
    background-color: #2f334d;
}}
QTableWidget {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    gridline-color: {DARK_BORDER};
    selection-background-color: {DARK_BORDER};
}}
QTableWidget QHeaderView::section {{
    background-color: {DARK_BG};
    color: {ACCENT};
    border: 1px solid {DARK_BORDER};
    padding: 4px;
    font-weight: bold;
}}
QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {DARK_BORDER};
    border-radius: 3px;
    background-color: {DARK_SURFACE};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QStatusBar {{
    background-color: {DARK_SURFACE};
    color: {TEXT_DIM};
    border-top: 1px solid {DARK_BORDER};
    font-size: 12px;
}}
QSplitter::handle {{
    background-color: {DARK_BORDER};
    width: 2px;
}}
QToolBar {{
    background-color: {DARK_SURFACE};
    border-bottom: 1px solid {DARK_BORDER};
    spacing: 4px;
    padding: 2px;
}}
QSpinBox {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QSpinBox:focus {{
    border-color: {ACCENT};
}}
QTextEdit {{
    background-color: {DARK_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {DARK_BORDER};
    border-radius: 4px;
    padding: 4px;
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
"""


# ---------------------------------------------------------------------------
# Matplotlib style — white background for paper-ready exports
# ---------------------------------------------------------------------------
def apply_mpl_dark_style():
    matplotlib.rcParams.update({
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "axes.edgecolor": DARK_BORDER,
        "axes.labelcolor": BLACK,
        "text.color": BLACK,
        "xtick.color": BLACK,
        "ytick.color": BLACK,
        "grid.color": DARK_BORDER,
        "grid.alpha": 0.5,
        "legend.facecolor": WHITE,
        "legend.edgecolor": DARK_BORDER,
        "font.family": "monospace",
        "font.size": 11,
    })


# ---------------------------------------------------------------------------
# Fit models
# ---------------------------------------------------------------------------
FIT_TYPES = [
    "None",
    "Linear  (a·x + b)",
    "Polynomial",
    "Exponential  (a·exp(b·x) + c)",
    "Power Law  (a·x^b + c)",
    "Logarithmic  (a·ln(x) + b)",
    "Gaussian  (a·exp(-(x-μ)²/2σ²) + c)",
    "Sine  (a·sin(b·x + c) + d)",
    "Custom Expression",
]

def _fit_linear(x, a, b):
    return a * x + b

def _fit_exponential(x, a, b, c):
    return a * np.exp(b * x) + c

def _fit_power(x, a, b, c):
    return a * np.power(x, b) + c

def _fit_log(x, a, b):
    return a * np.log(x) + b

def _fit_gaussian(x, a, mu, sigma, c):
    return a * np.exp(-0.5 * ((x - mu) / sigma) ** 2) + c

def _fit_sine(x, a, b, c, d):
    return a * np.sin(b * x + c) + d


def compute_r_squared(y_data, y_fit):
    ss_res = np.sum((y_data - y_fit) ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - ss_res / ss_tot


def compute_chi_squared_red(y_data, y_fit, n_params):
    dof = len(y_data) - n_params
    if dof <= 0:
        return np.nan
    return np.sum((y_data - y_fit) ** 2) / dof


def format_param(val, err=None):
    if err is not None and err > 0:
        mag = int(np.floor(np.log10(abs(err)))) if err != 0 else 0
        dec = max(0, -mag + 1)
        return f"{val:.{dec}f} ± {err:.{dec}f}"
    return f"{val:.6g}"


def perform_fit(x, y, fit_type, poly_degree=2, custom_expr=""):
    """
    Returns: (x_fit, y_fit_dense, params_dict, equation_str, y_pred, x_used, y_used)
    x_used, y_used may differ from x,y for power/log fits that filter x>0.
    """
    from collections import OrderedDict

    x_fit = np.linspace(x.min(), x.max(), 500)
    params = OrderedDict()
    x_used, y_used = x, y  # default: use all data

    if fit_type.startswith("Linear"):
        popt, pcov = curve_fit(_fit_linear, x, y)
        perr = np.sqrt(np.diag(pcov))
        y_dense = _fit_linear(x_fit, *popt)
        y_pred = _fit_linear(x, *popt)
        params["a (slope)"] = (popt[0], perr[0])
        params["b (intercept)"] = (popt[1], perr[1])
        eq = f"y = {popt[0]:.6g}·x + {popt[1]:.6g}"

    elif fit_type.startswith("Polynomial"):
        coeffs = np.polyfit(x, y, poly_degree)
        poly = np.poly1d(coeffs)
        y_dense = poly(x_fit)
        y_pred = poly(x)
        for i, c in enumerate(coeffs):
            power = poly_degree - i
            params[f"a_{power}"] = (c, None)
        terms = []
        for i, c in enumerate(coeffs):
            power = poly_degree - i
            if power > 1:
                terms.append(f"{c:.4g}·x^{power}")
            elif power == 1:
                terms.append(f"{c:.4g}·x")
            else:
                terms.append(f"{c:.4g}")
        eq = "y = " + " + ".join(terms)

    elif fit_type.startswith("Exponential"):
        y_range = y.max() - y.min()
        p0 = [y_range if y_range != 0 else 1.0, 0.01, y.min()]
        try:
            popt, pcov = curve_fit(_fit_exponential, x, y, p0=p0, maxfev=10000)
        except RuntimeError:
            p0 = [1.0, -0.1, np.mean(y)]
            popt, pcov = curve_fit(_fit_exponential, x, y, p0=p0, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        y_dense = _fit_exponential(x_fit, *popt)
        y_pred = _fit_exponential(x, *popt)
        params["a (amplitude)"] = (popt[0], perr[0])
        params["b (rate)"] = (popt[1], perr[1])
        params["c (offset)"] = (popt[2], perr[2])
        eq = f"y = {popt[0]:.4g}·exp({popt[1]:.4g}·x) + {popt[2]:.4g}"

    elif fit_type.startswith("Power"):
        mask = x > 0
        if np.sum(mask) < 3:
            raise ValueError("Power law fit requires positive X values (need ≥3 points with x>0)")
        x_used, y_used = x[mask], y[mask]
        p0 = [1.0, 1.0, 0.0]
        popt, pcov = curve_fit(_fit_power, x_used, y_used, p0=p0, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        x_fit = x_fit[x_fit > 0]
        y_dense = _fit_power(x_fit, *popt)
        y_pred = _fit_power(x_used, *popt)
        params["a (coefficient)"] = (popt[0], perr[0])
        params["b (exponent)"] = (popt[1], perr[1])
        params["c (offset)"] = (popt[2], perr[2])
        eq = f"y = {popt[0]:.4g}·x^{popt[1]:.4g} + {popt[2]:.4g}"

    elif fit_type.startswith("Logarithmic"):
        mask = x > 0
        if np.sum(mask) < 3:
            raise ValueError("Log fit requires positive X values (need ≥3 points with x>0)")
        x_used, y_used = x[mask], y[mask]
        popt, pcov = curve_fit(_fit_log, x_used, y_used)
        perr = np.sqrt(np.diag(pcov))
        x_fit = x_fit[x_fit > 0]
        y_dense = _fit_log(x_fit, *popt)
        y_pred = _fit_log(x_used, *popt)
        params["a (coefficient)"] = (popt[0], perr[0])
        params["b (offset)"] = (popt[1], perr[1])
        eq = f"y = {popt[0]:.4g}·ln(x) + {popt[1]:.4g}"

    elif fit_type.startswith("Gaussian"):
        mu0 = x[np.argmax(y)]
        sigma0 = (x.max() - x.min()) / 4
        a0 = y.max() - y.min()
        c0 = y.min()
        p0 = [a0 if a0 != 0 else 1.0, mu0, sigma0 if sigma0 != 0 else 1.0, c0]
        popt, pcov = curve_fit(_fit_gaussian, x, y, p0=p0, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        y_dense = _fit_gaussian(x_fit, *popt)
        y_pred = _fit_gaussian(x, *popt)
        params["a (amplitude)"] = (popt[0], perr[0])
        params["μ (center)"] = (popt[1], perr[1])
        params["σ (width)"] = (popt[2], perr[2])
        params["c (offset)"] = (popt[3], perr[3])
        eq = f"y = {popt[0]:.4g}·exp(-(x-{popt[1]:.4g})²/(2·{popt[2]:.4g}²)) + {popt[3]:.4g}"

    elif fit_type.startswith("Sine"):
        n = len(y)
        if n > 4:
            dx = np.median(np.diff(x))
            if dx == 0:
                dx = 1.0
            yf = np.fft.rfft(y - np.mean(y))
            freqs = np.fft.rfftfreq(n, d=dx)
            idx = np.argmax(np.abs(yf[1:])) + 1
            freq_guess = freqs[idx] * 2 * np.pi
        else:
            freq_guess = 2 * np.pi / (x.max() - x.min()) if x.max() != x.min() else 1.0
        a0 = (y.max() - y.min()) / 2
        d0 = np.mean(y)
        p0 = [a0 if a0 != 0 else 1.0, freq_guess, 0.0, d0]
        popt, pcov = curve_fit(_fit_sine, x, y, p0=p0, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        y_dense = _fit_sine(x_fit, *popt)
        y_pred = _fit_sine(x, *popt)
        params["a (amplitude)"] = (popt[0], perr[0])
        params["b (frequency)"] = (popt[1], perr[1])
        params["c (phase)"] = (popt[2], perr[2])
        params["d (offset)"] = (popt[3], perr[3])
        eq = f"y = {popt[0]:.4g}·sin({popt[1]:.4g}·x + {popt[2]:.4g}) + {popt[3]:.4g}"

    elif fit_type.startswith("Custom"):
        if not custom_expr.strip():
            raise ValueError(
                "Enter a custom expression using variable 'x' and parameters a,b,c,d,e.\n"
                "Examples:\n"
                "  a*x**2 + b*sin(c*x)\n"
                "  a*exp(-b*x)*cos(c*x + d)\n"
                "Available: sin cos tan exp log log10 sqrt abs sinh cosh tanh arcsin arccos arctan pi e"
            )
        safe_ns = {
            "np": np, "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "exp": np.exp, "log": np.log, "log10": np.log10, "log2": np.log2,
            "sqrt": np.sqrt, "abs": np.abs, "pi": np.pi, "e": np.e,
            "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
            "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan,
            "power": np.power,
        }
        all_params = ["a", "b", "c", "d", "e"]
        used_params = []
        for p in all_params:
            if re.search(rf'(?<![a-zA-Z_]){p}(?![a-zA-Z_0-9])', custom_expr):
                used_params.append(p)
        if not used_params:
            raise ValueError("Expression must contain at least one fit parameter (a, b, c, d, or e)")

        def custom_func(x_val, *args):
            ns = dict(safe_ns)
            ns["x"] = x_val
            for i, pname in enumerate(used_params):
                ns[pname] = args[i]
            return eval(custom_expr, {"__builtins__": {}}, ns)

        p0 = [1.0] * len(used_params)
        popt, pcov = curve_fit(custom_func, x, y, p0=p0, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        y_dense = custom_func(x_fit, *popt)
        y_pred = custom_func(x, *popt)
        for i, pname in enumerate(used_params):
            params[pname] = (popt[i], perr[i])
        eq_str = custom_expr
        for i, pname in enumerate(used_params):
            eq_str = re.sub(rf'(?<![a-zA-Z_]){pname}(?![a-zA-Z_0-9])',
                            f"{popt[i]:.4g}", eq_str, count=1)
        eq = f"y = {eq_str}"

    else:
        raise ValueError(f"Unknown fit type: {fit_type}")

    return x_fit, y_dense, params, eq, y_pred, x_used, y_used


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------
def _extract_comment_header(filepath: str):
    """
    Scan the file for a leading comment line like '# x  y  z' or '#x,y,z'.
    Returns the parsed column names list, or None if no such header exists.
    Only the LAST comment line before data is treated as a potential header
    (handles files with multiple comment lines at the top).
    """
    last_comment = None
    with open(filepath, "r", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                last_comment = stripped
            else:
                break  # first data line reached

    if last_comment is None:
        return None

    # Strip the '#' prefix (and optional '!' for Fortran-style)
    header_text = last_comment.lstrip("#!").strip()
    if not header_text:
        return None

    # Try splitting by common delimiters
    if "," in header_text:
        names = [n.strip() for n in header_text.split(",")]
    elif "\t" in header_text:
        names = [n.strip() for n in header_text.split("\t")]
    else:
        names = header_text.split()

    # Sanity check: header should have non-numeric tokens
    numeric_count = sum(1 for n in names if not _is_non_numeric(n))
    if numeric_count == len(names):
        return None  # all numeric → not a header

    return names if names else None


def _parse_whitespace_delimited(filepath: str, comment_header):
    """Parse a whitespace-delimited file (e.g. .dat, .txt, Fortran output, CLASS, Cobaya chains)."""
    rows = []
    with open(filepath, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(line.split())
    if not rows:
        return [], []

    if comment_header:
        ncols = len(rows[0])
        if len(comment_header) < ncols:
            comment_header += [f"col_{i}" for i in range(len(comment_header), ncols)]
        return comment_header[:ncols], rows

    try:
        [float(v) for v in rows[0]]
        return [f"col_{i}" for i in range(len(rows[0]))], rows
    except ValueError:
        return rows[0], rows[1:]


def load_data(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()

    # First, check for a #-prefixed header line
    comment_header = _extract_comment_header(filepath)

    # For non-CSV/TSV files, always use whitespace splitting.
    # The csv.Sniffer is too aggressive and mis-detects delimiters
    # in scientific data (spaces, periods in decimals, etc.).
    if ext not in (".csv", ".tsv"):
        return _parse_whitespace_delimited(filepath, comment_header)

    # CSV / TSV path
    with open(filepath, "r", errors="replace") as f:
        if ext == ".tsv":
            reader = csv.reader(f, delimiter="\t")
        else:
            reader = csv.reader(f)

        all_rows = []
        for row in reader:
            stripped = [c.strip() for c in row]
            if not stripped:
                continue
            if stripped[0].startswith("#"):
                continue
            all_rows.append(stripped)

    if not all_rows:
        return [], []

    # If we found a # header, use it
    if comment_header:
        ncols = len(all_rows[0])
        if len(comment_header) < ncols:
            comment_header += [f"col_{i}" for i in range(len(comment_header), ncols)]
        return comment_header[:ncols], all_rows

    # Otherwise, check if the first row is a non-comment header
    first = all_rows[0]
    is_header = any(True for v in first if _is_non_numeric(v))
    if is_header:
        return first, all_rows[1:]
    else:
        return [f"col_{i}" for i in range(len(first))], all_rows


def _is_non_numeric(s):
    try:
        float(s)
        return False
    except ValueError:
        return True


# ---------------------------------------------------------------------------
# Streaming data loader (runs in a background QThread)
# ---------------------------------------------------------------------------
CHUNK_SIZE = 5000  # rows per chunk


class DataLoaderWorker(QThread):
    """
    Loads a data file in chunks on a background thread.

    Signals:
        headers_ready(list)   — emitted once when headers are determined
        chunk_ready(list)     — emitted every CHUNK_SIZE rows with a batch of rows
        progress(int, int)    — (rows_loaded_so_far, total_lines_estimate)
        finished(int)         — total row count when done
        error(str)            — error message if something goes wrong
    """
    headers_ready = pyqtSignal(list)
    chunk_ready = pyqtSignal(list)
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, filepath, parent=None):
        super().__init__(parent)
        self.filepath = filepath

    def run(self):
        try:
            filepath = self.filepath
            ext = os.path.splitext(filepath)[1].lower()

            # Estimate total lines for progress bar
            total_estimate = 0
            try:
                with open(filepath, "r", errors="replace") as f:
                    # Fast line count: read in 1MB blocks
                    buf_size = 1024 * 1024
                    buf = f.read(buf_size)
                    while buf:
                        total_estimate += buf.count("\n")
                        buf = f.read(buf_size)
            except Exception:
                total_estimate = 0

            # Extract comment header
            comment_header = _extract_comment_header(filepath)

            headers = None
            chunk = []
            rows_loaded = 0

            if ext in (".csv", ".tsv"):
                # CSV/TSV path
                with open(filepath, "r", errors="replace") as f:
                    delimiter = "\t" if ext == ".tsv" else ","
                    reader = csv.reader(f, delimiter=delimiter)
                    for row in reader:
                        if self.isInterruptionRequested():
                            return
                        stripped = [c.strip() for c in row]
                        if not stripped:
                            continue
                        if stripped[0].startswith("#"):
                            continue

                        # First data row: determine headers
                        if headers is None:
                            if comment_header:
                                ncols = len(stripped)
                                h = list(comment_header)
                                if len(h) < ncols:
                                    h += [f"col_{i}" for i in range(len(h), ncols)]
                                headers = h[:ncols]
                            else:
                                is_hdr = any(_is_non_numeric(v) for v in stripped)
                                if is_hdr:
                                    headers = stripped
                                    self.headers_ready.emit(headers)
                                    continue  # this row is the header, skip adding to data
                                else:
                                    headers = [f"col_{i}" for i in range(len(stripped))]
                            self.headers_ready.emit(headers)

                        chunk.append(stripped)
                        rows_loaded += 1

                        if len(chunk) >= CHUNK_SIZE:
                            self.chunk_ready.emit(chunk)
                            self.progress.emit(rows_loaded, total_estimate)
                            chunk = []
            else:
                # Whitespace-delimited path
                with open(filepath, "r", errors="replace") as f:
                    for line in f:
                        if self.isInterruptionRequested():
                            return
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        fields = line.split()

                        if headers is None:
                            if comment_header:
                                ncols = len(fields)
                                h = list(comment_header)
                                if len(h) < ncols:
                                    h += [f"col_{i}" for i in range(len(h), ncols)]
                                headers = h[:ncols]
                            else:
                                try:
                                    [float(v) for v in fields]
                                    headers = [f"col_{i}" for i in range(len(fields))]
                                except ValueError:
                                    headers = fields
                                    self.headers_ready.emit(headers)
                                    continue
                            self.headers_ready.emit(headers)

                        chunk.append(fields)
                        rows_loaded += 1

                        if len(chunk) >= CHUNK_SIZE:
                            self.chunk_ready.emit(chunk)
                            self.progress.emit(rows_loaded, total_estimate)
                            chunk = []

            # Emit remaining rows
            if chunk:
                self.chunk_ready.emit(chunk)

            # Edge case: file had no data rows
            if headers is None:
                self.error.emit("No data rows found in file.")
                return

            self.progress.emit(rows_loaded, rows_loaded)
            self.finished.emit(rows_loaded)

        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class ModernPlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ModernPlot — Interactive Data Plotter")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self.headers = []
        self.raw_data = []
        self.np_data = None   # 2D float64 array, built once after loading
        self.filepath = ""
        self.last_fit_result = None
        self.worker = None  # background data loader thread

        self._build_ui()
        self.statusBar().showMessage("Ready — open a data file to begin")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        toolbar.addSeparator()

        self.file_label = QLabel("  No file loaded")
        self.file_label.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic;")
        toolbar.addWidget(self.file_label)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # ---- Left Panel (scrollable) ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 6, 10)
        left_layout.setSpacing(8)
        scroll.setWidget(left_panel)
        scroll.setMaximumWidth(360)
        scroll.setMinimumWidth(280)

        # ── Data Source ──
        file_group = QGroupBox("Data Source")
        fg_layout = QVBoxLayout(file_group)
        btn_open = QPushButton("Open File …")
        btn_open.clicked.connect(self.open_file)
        fg_layout.addWidget(btn_open)

        # Progress bar (hidden until loading)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Loading… %v rows")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {DARK_BORDER};
                border-radius: 4px;
                background-color: {DARK_SURFACE};
                color: {TEXT_PRIMARY};
                text-align: center;
                font-size: 11px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.hide()
        fg_layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(f"QPushButton {{ background-color: {RED}; color: {DARK_BG}; border: none; padding: 4px 12px; }}")
        self.cancel_btn.clicked.connect(self._cancel_loading)
        self.cancel_btn.hide()
        fg_layout.addWidget(self.cancel_btn)

        self.table = QTableWidget()
        self.table.setMaximumHeight(140)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        fg_layout.addWidget(self.table)
        left_layout.addWidget(file_group)

        # ── Column selection ──
        col_group = QGroupBox("Columns")
        cg_layout = QGridLayout(col_group)
        cg_layout.addWidget(QLabel("X axis:"), 0, 0)
        self.x_combo = QComboBox()
        cg_layout.addWidget(self.x_combo, 0, 1)
        cg_layout.addWidget(QLabel("Y axis:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        # Y axis checkboxes in a scroll area
        self.y_check_container = QWidget()
        self.y_check_layout = QVBoxLayout(self.y_check_container)
        self.y_check_layout.setContentsMargins(4, 4, 4, 4)
        self.y_check_layout.setSpacing(2)
        self.y_checkboxes = []  # list of QCheckBox

        y_scroll = QScrollArea()
        y_scroll.setWidgetResizable(True)
        y_scroll.setWidget(self.y_check_container)
        y_scroll.setMaximumHeight(120)
        y_scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {DARK_BORDER}; border-radius: 4px; background: {DARK_SURFACE}; }}"
        )
        cg_layout.addWidget(y_scroll, 1, 1)
        left_layout.addWidget(col_group)

        # ── Plot options ──
        opt_group = QGroupBox("Plot Options")
        og_layout = QGridLayout(opt_group)
        og_layout.addWidget(QLabel("Type:"), 0, 0)
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Line", "Scatter", "Line + Scatter", "Step", "Bar"])
        og_layout.addWidget(self.plot_type_combo, 0, 1)
        og_layout.addWidget(QLabel("X scale:"), 1, 0)
        self.xscale_combo = QComboBox()
        self.xscale_combo.addItems(["linear", "log", "symlog"])
        og_layout.addWidget(self.xscale_combo, 1, 1)
        og_layout.addWidget(QLabel("Y scale:"), 2, 0)
        self.yscale_combo = QComboBox()
        self.yscale_combo.addItems(["linear", "log", "symlog"])
        og_layout.addWidget(self.yscale_combo, 2, 1)
        self.grid_check = QCheckBox("Show grid")
        self.grid_check.setChecked(True)
        og_layout.addWidget(self.grid_check, 3, 0, 1, 2)
        self.legend_check = QCheckBox("Show legend")
        self.legend_check.setChecked(True)
        og_layout.addWidget(self.legend_check, 4, 0, 1, 2)
        left_layout.addWidget(opt_group)

        # ── Curve Fitting ──
        fit_group = QGroupBox("Curve Fitting")
        fit_layout = QGridLayout(fit_group)

        fit_layout.addWidget(QLabel("Fit type:"), 0, 0)
        self.fit_combo = QComboBox()
        self.fit_combo.addItems(FIT_TYPES)
        self.fit_combo.currentTextChanged.connect(self._on_fit_type_changed)
        fit_layout.addWidget(self.fit_combo, 0, 1)

        self.poly_degree_label = QLabel("Degree:")
        self.poly_degree_spin = QSpinBox()
        self.poly_degree_spin.setRange(2, 15)
        self.poly_degree_spin.setValue(2)
        fit_layout.addWidget(self.poly_degree_label, 1, 0)
        fit_layout.addWidget(self.poly_degree_spin, 1, 1)
        self.poly_degree_label.hide()
        self.poly_degree_spin.hide()

        self.custom_label = QLabel("f(x) =")
        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText("a*x**2 + b*sin(c*x)")
        fit_layout.addWidget(self.custom_label, 2, 0)
        fit_layout.addWidget(self.custom_edit, 2, 1)
        self.custom_label.hide()
        self.custom_edit.hide()

        fit_layout.addWidget(QLabel("Fit Y:"), 3, 0)
        self.fit_y_combo = QComboBox()
        self.fit_y_combo.setToolTip("Which Y series to fit (uses first selected Y if empty)")
        fit_layout.addWidget(self.fit_y_combo, 3, 1)

        self.show_residuals_check = QCheckBox("Show residuals subplot")
        self.show_residuals_check.setChecked(False)
        fit_layout.addWidget(self.show_residuals_check, 4, 0, 1, 2)

        self.show_equation_check = QCheckBox("Show equation on plot")
        self.show_equation_check.setChecked(True)
        fit_layout.addWidget(self.show_equation_check, 5, 0, 1, 2)

        self.show_ci_check = QCheckBox("Show confidence band")
        self.show_ci_check.setChecked(False)
        fit_layout.addWidget(self.show_ci_check, 6, 0, 1, 2)

        fit_layout.addWidget(QLabel("Fit scale:"), 7, 0)
        self.fit_scale_combo = QComboBox()
        self.fit_scale_combo.addItems([
            "linear",
            "log₁₀-log₁₀",
            "ln-ln",
            "semilog-x  log₁₀(X)",
            "semilog-x  ln(X)",
            "semilog-y  log₁₀(Y)",
            "semilog-y  ln(Y)",
        ])
        self.fit_scale_combo.setToolTip(
            "Transform data before fitting:\n"
            "  linear — fit raw x, y\n"
            "  log₁₀-log₁₀ — fit log₁₀(x), log₁₀(y)\n"
            "  ln-ln — fit ln(x), ln(y)\n"
            "  semilog-x — fit log/ln(x), y\n"
            "  semilog-y — fit x, log/ln(y)  ← use ln(Y) when X is already ln(k)"
        )
        fit_layout.addWidget(self.fit_scale_combo, 7, 1)

        left_layout.addWidget(fit_group)

        # ── Labels ──
        label_group = QGroupBox("Labels")
        lg_layout = QGridLayout(label_group)
        lg_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Plot title")
        lg_layout.addWidget(self.title_edit, 0, 1)
        lg_layout.addWidget(QLabel("X label:"), 1, 0)
        self.xlabel_edit = QLineEdit()
        self.xlabel_edit.setPlaceholderText("X axis label")
        lg_layout.addWidget(self.xlabel_edit, 1, 1)
        lg_layout.addWidget(QLabel("Y label:"), 2, 0)
        self.ylabel_edit = QLineEdit()
        self.ylabel_edit.setPlaceholderText("Y axis label")
        lg_layout.addWidget(self.ylabel_edit, 2, 1)
        left_layout.addWidget(label_group)

        # ── Buttons ──
        btn_row1 = QHBoxLayout()
        plot_btn = QPushButton("Plot")
        plot_btn.setObjectName("plotBtn")
        plot_btn.clicked.connect(self.do_plot)
        btn_row1.addWidget(plot_btn)
        fit_btn = QPushButton("Plot + Fit")
        fit_btn.setObjectName("fitBtn")
        fit_btn.clicked.connect(self.do_fit)
        btn_row1.addWidget(fit_btn)
        left_layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.setObjectName("exportBtn")
        export_btn.clicked.connect(self.export_plot)
        btn_row2.addWidget(export_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_plot)
        btn_row2.addWidget(clear_btn)
        left_layout.addLayout(btn_row2)

        # ── Fit Results ──
        results_group = QGroupBox("Fit Results")
        rg_layout = QVBoxLayout(results_group)
        self.fit_results_text = QTextEdit()
        self.fit_results_text.setReadOnly(True)
        self.fit_results_text.setMaximumHeight(200)
        self.fit_results_text.setPlaceholderText("Fit results will appear here…")
        rg_layout.addWidget(self.fit_results_text)

        copy_btn = QPushButton("Copy Results")
        copy_btn.clicked.connect(self._copy_fit_results)
        rg_layout.addWidget(copy_btn)
        left_layout.addWidget(results_group)

        left_layout.addStretch()

        # ---- Right Panel: Canvas ----
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 10, 10)

        apply_mpl_dark_style()
        self.figure = Figure(dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.nav_toolbar = NavigationToolbar(self.canvas, self)
        self.nav_toolbar.setStyleSheet(
            f"background-color: {DARK_SURFACE}; border: 1px solid {DARK_BORDER}; border-radius: 4px;"
        )

        right_layout.addWidget(self.nav_toolbar)
        right_layout.addWidget(self.canvas, 1)

        # Welcome
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "ModernPlot", transform=ax.transAxes,
                ha="center", va="center", fontsize=36, color="#cccccc",
                fontfamily="monospace", fontweight="bold")
        ax.text(0.5, 0.38, "Open a file to get started", transform=ax.transAxes,
                ha="center", va="center", fontsize=13, color="#999999",
                fontfamily="monospace")
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()

        splitter.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([340, 1060])

        self.setStatusBar(QStatusBar())

    # ----- Handlers -----
    def _on_fit_type_changed(self, text):
        self.poly_degree_label.setVisible(text.startswith("Polynomial"))
        self.poly_degree_spin.setVisible(text.startswith("Polynomial"))
        self.custom_label.setVisible(text.startswith("Custom"))
        self.custom_edit.setVisible(text.startswith("Custom"))

    def _copy_fit_results(self):
        text = self.fit_results_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("Fit results copied to clipboard")

    # ----- File handling -----
    def open_file(self):
        # If a load is in progress, cancel it first
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(2000)

        path, _ = QFileDialog.getOpenFileName(
            self, "Open Data File", "",
            "All supported (*.csv *.tsv *.dat *.txt *.asc);;CSV (*.csv);;TSV (*.tsv);;DAT (*.dat);;Text (*.txt);;All (*)"
        )
        if not path:
            return

        # Reset state
        self.filepath = path
        self.headers = []
        self.raw_data = []
        self.np_data = None
        self.last_fit_result = None

        # Clear table and selectors
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        # Show loading screen IMMEDIATELY
        fname = os.path.basename(path)
        fsize = os.path.getsize(path)
        if fsize > 1024 * 1024:
            size_str = f"{fsize / (1024*1024):.1f} MB"
        elif fsize > 1024:
            size_str = f"{fsize / 1024:.0f} KB"
        else:
            size_str = f"{fsize} B"

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.55, "Loading", transform=ax.transAxes,
                ha="center", va="center", fontsize=28, color="#aaaaaa",
                fontfamily="monospace", fontweight="bold")
        ax.text(0.5, 0.43, fname, transform=ax.transAxes,
                ha="center", va="center", fontsize=13, color="#888888",
                fontfamily="monospace")
        ax.text(0.5, 0.34, size_str, transform=ax.transAxes,
                ha="center", va="center", fontsize=11, color="#bbbbbb",
                fontfamily="monospace")
        self.canvas.draw()

        self.file_label.setText(f"  Loading {fname}…")
        self.file_label.setStyleSheet(f"color: {ORANGE}; font-style: italic;")
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()

        # Force Qt to paint everything NOW before we block on the loader
        QApplication.processEvents()

        # Defer actual loading to next event loop cycle so the screen paints
        QTimer.singleShot(50, lambda: self._do_load(path))

    def _do_load(self, path):
        """Called after loading screen is visible. Dispatch to C++ or Python loader."""
        if HAS_FAST_LOADER:
            self._open_file_cpp(path)
        else:
            self._open_file_streaming(path)

    def _open_file_cpp(self, path):
        """Load file using C++ fast_loader — synchronous but very fast."""
        fname = os.path.basename(path)

        try:
            headers, np_data = _fast_loader.load(path)
        except Exception as e:
            self.progress_bar.hide()
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
            self.file_label.setText("  Load failed")
            self.file_label.setStyleSheet(f"color: {RED}; font-style: italic;")
            return

        self.headers = headers
        self.np_data = np_data
        nrows, ncols = np_data.shape

        # Populate table preview (first 50 rows)
        self._populate_table_from_numpy()
        self._populate_column_selectors()

        self.progress_bar.hide()
        self.file_label.setText(
            f"  {fname}  ({nrows:,} rows × {ncols} cols)  [C++]"
        )
        self.file_label.setStyleSheet(f"color: {GREEN}; font-style: normal; font-weight: bold;")
        self.statusBar().showMessage(
            f"Loaded {fname}: {nrows:,} rows, {ncols} columns (C++ fast loader)"
        )

        # Show summary on canvas
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.58, fname, transform=ax.transAxes,
                ha="center", va="center", fontsize=18, color="#666666",
                fontfamily="monospace", fontweight="bold")
        ax.text(0.5, 0.47, f"{nrows:,} rows  ×  {ncols} columns", transform=ax.transAxes,
                ha="center", va="center", fontsize=13, color="#888888",
                fontfamily="monospace")
        col_list = ", ".join(headers[:6])
        if len(headers) > 6:
            col_list += f", … (+{len(headers)-6} more)"
        ax.text(0.5, 0.38, col_list, transform=ax.transAxes,
                ha="center", va="center", fontsize=10, color="#aaaaaa",
                fontfamily="monospace")
        ax.text(0.5, 0.28, "Select columns and click Plot", transform=ax.transAxes,
                ha="center", va="center", fontsize=11, color="#bbbbbb",
                fontfamily="monospace")
        self.canvas.draw()

    def _populate_table_from_numpy(self):
        """Fill table preview from self.np_data (first 50 rows)."""
        if self.np_data is None:
            return
        nrows = min(self.np_data.shape[0], 50)
        ncols = self.np_data.shape[1]
        self.table.setRowCount(nrows)
        self.table.setColumnCount(ncols)
        self.table.setHorizontalHeaderLabels(self.headers)
        for r in range(nrows):
            for c in range(ncols):
                val = self.np_data[r, c]
                text = f"{val:.6g}" if not np.isnan(val) else ""
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()

    def _open_file_streaming(self, path):
        """Fallback: load file using Python streaming QThread loader."""
        fname = os.path.basename(path)

        # Show loading screen on canvas
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.55, "Loading", transform=ax.transAxes,
                ha="center", va="center", fontsize=28, color="#aaaaaa",
                fontfamily="monospace", fontweight="bold")
        ax.text(0.5, 0.43, fname, transform=ax.transAxes,
                ha="center", va="center", fontsize=13, color="#888888",
                fontfamily="monospace")
        ax.text(0.5, 0.34, "(Python streaming loader)", transform=ax.transAxes,
                ha="center", va="center", fontsize=10, color="#bbbbbb",
                fontfamily="monospace")
        self.canvas.draw()

        # Show progress UI
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.show()
        self.cancel_btn.show()
        self.file_label.setText(f"  Loading {fname}…")
        self.file_label.setStyleSheet(f"color: {ORANGE}; font-style: italic;")

        # Start background worker
        self.worker = DataLoaderWorker(path)
        self.worker.headers_ready.connect(self._on_headers_ready)
        self.worker.chunk_ready.connect(self._on_chunk_ready)
        self.worker.progress.connect(self._on_load_progress)
        self.worker.finished.connect(self._on_load_finished)
        self.worker.error.connect(self._on_load_error)
        self.worker.start()

    def _cancel_loading(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.requestInterruption()
            self.statusBar().showMessage("Cancelling…")

    def _on_headers_ready(self, headers):
        """Called once when the worker determines column headers."""
        self.headers = headers
        self._populate_column_selectors()
        # Set up table columns
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def _on_chunk_ready(self, chunk):
        """Called every CHUNK_SIZE rows with a batch of parsed rows."""
        start_row = len(self.raw_data)
        self.raw_data.extend(chunk)

        # Update table preview (only first 50 rows)
        if start_row < 50:
            end = min(start_row + len(chunk), 50)
            self.table.setRowCount(min(len(self.raw_data), 50))
            for r in range(start_row, end):
                row = self.raw_data[r]
                for c, val in enumerate(row):
                    if c < self.table.columnCount():
                        self.table.setItem(r, c, QTableWidgetItem(str(val)))
            if start_row == 0:
                self.table.resizeColumnsToContents()

    def _on_load_progress(self, loaded, total):
        """Update progress bar."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(loaded)
            self.progress_bar.setFormat(f"Loading… {loaded:,} / ~{total:,} rows")
        else:
            self.progress_bar.setFormat(f"Loading… {loaded:,} rows")

    def _on_load_finished(self, total_rows):
        """Called when loading completes. Convert to numpy for fast plotting."""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Converting to numeric…")

        ncols = len(self.headers)
        nrows = len(self.raw_data)
        arr = np.empty((nrows, ncols), dtype=np.float64)
        arr[:] = np.nan

        # Convert in chunks so UI stays responsive
        chunk = 50000
        for start in range(0, nrows, chunk):
            end = min(start + chunk, nrows)
            for r in range(start, end):
                row = self.raw_data[r]
                for c in range(min(len(row), ncols)):
                    try:
                        arr[r, c] = float(row[c])
                    except (ValueError, IndexError):
                        pass
            pct = int(100 * end / nrows)
            self.progress_bar.setValue(pct)
            QApplication.processEvents()

        self.np_data = arr
        # Free string data
        self.raw_data = []

        self.progress_bar.hide()
        self.cancel_btn.hide()
        self.file_label.setText(
            f"  {os.path.basename(self.filepath)}  ({total_rows:,} rows × {ncols} cols)"
        )
        self.file_label.setStyleSheet(f"color: {GREEN}; font-style: normal; font-weight: bold;")
        self.statusBar().showMessage(
            f"Loaded {os.path.basename(self.filepath)}: {total_rows:,} rows, {ncols} columns"
        )

    def _on_load_error(self, msg):
        """Called if loading fails."""
        self.progress_bar.hide()
        self.cancel_btn.hide()
        self.file_label.setText("  Load failed")
        self.file_label.setStyleSheet(f"color: {RED}; font-style: italic;")
        QMessageBox.critical(self, "Error", f"Failed to load file:\n{msg}")

    def _populate_column_selectors(self):
        self.x_combo.clear()
        self.fit_y_combo.clear()

        # Clear old Y checkboxes
        for cb in self.y_checkboxes:
            self.y_check_layout.removeWidget(cb)
            cb.deleteLater()
        self.y_checkboxes = []

        self.x_combo.addItem("(row index)")
        for h in self.headers:
            self.x_combo.addItem(h)
            self.fit_y_combo.addItem(h)

            cb = QCheckBox(h)
            cb.setStyleSheet(f"QCheckBox {{ color: {TEXT_PRIMARY}; padding: 1px 0; }}")
            self.y_check_layout.addWidget(cb)
            self.y_checkboxes.append(cb)

        if len(self.headers) >= 2:
            self.x_combo.setCurrentIndex(1)
            self.y_checkboxes[1].setChecked(True)
            self.fit_y_combo.setCurrentIndex(1)
        elif len(self.headers) == 1:
            self.y_checkboxes[0].setChecked(True)

    # ----- Data -----
    def _get_column_data(self, col_name):
        if self.np_data is None or len(self.np_data) == 0:
            return np.array([])
        if col_name == "(row index)":
            return np.arange(self.np_data.shape[0], dtype=float)
        idx = self.headers.index(col_name)
        return self.np_data[:, idx].copy()

    def _get_selected_y(self):
        """Return list of checked Y column names."""
        return [cb.text() for cb in self.y_checkboxes if cb.isChecked()]

    # ----- Plot helpers -----
    def _plot_data_on_ax(self, ax):
        selected_y = self._get_selected_y()
        if not selected_y:
            return
        x_col = self.x_combo.currentText()
        plot_type = self.plot_type_combo.currentText()
        x_data = self._get_column_data(x_col)

        MAX_PLOT_POINTS = 15000

        for i, y_col in enumerate(selected_y):
            try:
                y_data = self._get_column_data(y_col)
            except Exception:
                continue
            color = PLOT_COLORS[i % len(PLOT_COLORS)]
            mask = ~(np.isnan(x_data) | np.isnan(y_data))
            xd, yd = x_data[mask], y_data[mask]

            # Downsample if too many points
            n = len(xd)
            if n > MAX_PLOT_POINTS:
                stride = n // MAX_PLOT_POINTS
                xd, yd = xd[::stride], yd[::stride]

            if plot_type == "Line":
                ax.plot(xd, yd, color=color, label=y_col, linewidth=1.5)
            elif plot_type == "Scatter":
                ax.scatter(xd, yd, color=color, label=y_col, s=18, alpha=0.8, edgecolors="none")
            elif plot_type == "Line + Scatter":
                ax.plot(xd, yd, color=color, label=y_col, linewidth=1.2,
                        marker="o", markersize=4, markerfacecolor=color, markeredgecolor="none")
            elif plot_type == "Step":
                ax.step(xd, yd, color=color, label=y_col, linewidth=1.5, where="mid")
            elif plot_type == "Bar":
                width = (xd.max() - xd.min()) / len(xd) * 0.8 if len(xd) > 1 else 1
                offset = width * (i - len(selected_y) / 2) / len(selected_y)
                ax.bar(xd + offset, yd, width=width / len(selected_y),
                       color=color, label=y_col, alpha=0.85)

    def _style_ax(self, ax, show_xlabel=True):
        ax.set_xscale(self.xscale_combo.currentText())
        ax.set_yscale(self.yscale_combo.currentText())
        selected_y = self._get_selected_y()
        title = self.title_edit.text()
        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
        if show_xlabel:
            ax.set_xlabel(self.xlabel_edit.text() or self.x_combo.currentText())
        ax.set_ylabel(self.ylabel_edit.text() or (selected_y[0] if len(selected_y) == 1 else ""))
        if self.grid_check.isChecked():
            ax.grid(True, alpha=0.3, linestyle="--")
        if self.legend_check.isChecked():
            ax.legend(framealpha=0.8, fontsize=10)

    # ----- Actions -----
    def do_plot(self):
        if self.np_data is None or len(self.np_data) == 0:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return
        selected_y = self._get_selected_y()
        if not selected_y:
            QMessageBox.warning(self, "No Y column", "Select at least one Y column.")
            return

        self.figure.clear()
        self.last_fit_result = None
        ax = self.figure.add_subplot(111)
        self._plot_data_on_ax(ax)
        self._style_ax(ax)
        self.figure.tight_layout()
        self.canvas.draw()
        self.statusBar().showMessage(
            f"Plotted {len(selected_y)} series  |  {self.plot_type_combo.currentText()}  |  "
            f"X: {self.xscale_combo.currentText()}  Y: {self.yscale_combo.currentText()}"
        )

    def do_fit(self):
        if self.np_data is None or len(self.np_data) == 0:
            QMessageBox.warning(self, "No data", "Load a file first.")
            return

        fit_type = self.fit_combo.currentText()
        if fit_type == "None":
            QMessageBox.information(self, "No fit", "Select a fit type from the dropdown.")
            return

        # Determine Y column to fit
        fit_y_col = self.fit_y_combo.currentText()
        if not fit_y_col:
            selected = self._get_selected_y()
            if not selected:
                QMessageBox.warning(self, "No Y", "Select a Y column to fit.")
                return
            fit_y_col = selected[0]

        x_col = self.x_combo.currentText()
        try:
            x_raw = self._get_column_data(x_col)
            y_raw = self._get_column_data(fit_y_col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read columns:\n{e}")
            return

        mask = ~(np.isnan(x_raw) | np.isnan(y_raw))
        x_clean = x_raw[mask]
        y_clean = y_raw[mask]
        if len(x_clean) < 3:
            QMessageBox.warning(self, "Insufficient data", "Need at least 3 valid data points.")
            return

        idx = np.argsort(x_clean)
        x_clean, y_clean = x_clean[idx], y_clean[idx]

        # ── Fit scale transform ──
        fit_scale = self.fit_scale_combo.currentText()

        # Determine which axes to transform and with which function
        transform_x = None  # None, "log10", or "ln"
        transform_y = None
        if "log₁₀-log₁₀" in fit_scale:
            transform_x, transform_y = "log10", "log10"
        elif "ln-ln" in fit_scale:
            transform_x, transform_y = "ln", "ln"
        elif "semilog-x" in fit_scale:
            transform_x = "ln" if "ln" in fit_scale else "log10"
        elif "semilog-y" in fit_scale:
            transform_y = "ln" if "ln" in fit_scale else "log10"

        log_x = transform_x is not None
        log_y = transform_y is not None

        def apply_log(arr, mode):
            return np.log(arr) if mode == "ln" else np.log10(arr)

        def label_log(mode):
            return "ln" if mode == "ln" else "log₁₀"

        x_to_fit = x_clean.copy()
        y_to_fit = y_clean.copy()

        if log_x or log_y:
            pos_mask = np.ones(len(x_to_fit), dtype=bool)
            if log_x:
                pos_mask &= (x_to_fit > 0)
            if log_y:
                pos_mask &= (y_to_fit > 0)

            if np.sum(pos_mask) < 3:
                QMessageBox.warning(
                    self, "Insufficient data",
                    f"Fit scale '{fit_scale}' requires positive values.\n"
                    f"Only {np.sum(pos_mask)} valid points after filtering."
                )
                return

            x_to_fit = x_to_fit[pos_mask]
            y_to_fit = y_to_fit[pos_mask]

            if log_x:
                x_to_fit = apply_log(x_to_fit, transform_x)
            if log_y:
                y_to_fit = apply_log(y_to_fit, transform_y)

        # Fit
        try:
            x_fit, y_dense, params, equation, y_pred, x_used, y_used = perform_fit(
                x_to_fit, y_to_fit, fit_type,
                poly_degree=self.poly_degree_spin.value(),
                custom_expr=self.custom_edit.text(),
            )
        except Exception as e:
            self.fit_results_text.setHtml(
                f'<span style="color:{RED}; font-weight:bold;">Fit failed</span><br>'
                f'<span style="color:{TEXT_DIM};">{e}</span>'
            )
            self.statusBar().showMessage("Fit failed — check results panel")
            return

        r_sq = compute_r_squared(y_used, y_pred)
        chi_red = compute_chi_squared_red(y_used, y_pred, len(params))
        residuals = y_used - y_pred
        rms = np.sqrt(np.mean(residuals ** 2))

        self.last_fit_result = dict(
            x_data=x_used, y_data=y_used, y_pred=y_pred,
            residuals=residuals, x_fit=x_fit, y_fit=y_dense,
        )

        # Build results HTML
        scale_label = fit_scale if fit_scale != "linear" else ""
        html = f'<span style="color:{ACCENT}; font-weight:bold; font-size:13px;">{fit_type}</span><br>'
        if scale_label:
            html += f'<span style="color:{CYAN}; font-size:11px;">fit scale: {scale_label}</span><br>'
        html += f'<span style="color:{ORANGE};">{equation}</span><br>'
        if log_x or log_y:
            vars_note = []
            if log_x:
                vars_note.append(f"x → {label_log(transform_x)}(x)")
            if log_y:
                vars_note.append(f"y → {label_log(transform_y)}(y)")
            html += f'<span style="color:{TEXT_DIM}; font-size:11px;">({", ".join(vars_note)})</span><br>'
        html += '<br><table cellpadding="2">'
        for name, (val, err) in params.items():
            html += (f'<tr><td style="color:{TEXT_DIM}; padding-right:10px;">{name}</td>'
                     f'<td style="color:{TEXT_PRIMARY};">{format_param(val, err)}</td></tr>')
        html += '</table><br>'
        r_color = GREEN if r_sq > 0.95 else (ORANGE if r_sq > 0.8 else RED)
        html += f'<span style="color:{r_color}; font-weight:bold;">R² = {r_sq:.8f}</span><br>'
        html += f'<span style="color:{TEXT_DIM};">χ²_red = {chi_red:.6g}  |  RMS = {rms:.6g}</span><br>'
        html += f'<span style="color:{TEXT_DIM};">N = {len(y_used)}  |  DoF = {len(y_used) - len(params)}</span>'
        self.fit_results_text.setHtml(html)

        # Draw
        self.figure.clear()
        show_resid = self.show_residuals_check.isChecked()

        if show_resid:
            gs = self.figure.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.08)
            ax_main = self.figure.add_subplot(gs[0])
            ax_resid = self.figure.add_subplot(gs[1], sharex=ax_main)
        else:
            ax_main = self.figure.add_subplot(111)

        # If log fit scale, plot the transformed data + fit; otherwise plot raw data
        if log_x or log_y:
            # Plot transformed data points
            selected_y = self._get_selected_y()
            ax_main.scatter(x_used, y_used, color=PLOT_COLORS[0], s=18, alpha=0.8,
                            edgecolors="none", label=fit_y_col, zorder=5)
            # Fit curve in transformed space
            ax_main.plot(x_fit, y_dense, color=FIT_COLOR, linewidth=2.2, linestyle="--",
                         label=f"Fit: {fit_type.split('(')[0].strip()}", zorder=10)
            # Axis labels
            x_label_base = self.xlabel_edit.text() or self.x_combo.currentText()
            y_label_base = self.ylabel_edit.text() or fit_y_col
            if log_x:
                ax_main.set_xlabel(f"{label_log(transform_x)}({x_label_base})")
            else:
                ax_main.set_xlabel(x_label_base)
            if log_y:
                ax_main.set_ylabel(f"{label_log(transform_y)}({y_label_base})")
            else:
                ax_main.set_ylabel(y_label_base)
            title = self.title_edit.text()
            if title:
                ax_main.set_title(title, fontsize=14, fontweight="bold", pad=10)
            if self.grid_check.isChecked():
                ax_main.grid(True, alpha=0.3, linestyle="--")
            if self.legend_check.isChecked():
                ax_main.legend(framealpha=0.8, fontsize=10)
        else:
            self._plot_data_on_ax(ax_main)
            ax_main.plot(x_fit, y_dense, color=FIT_COLOR, linewidth=2.2, linestyle="--",
                         label=f"Fit: {fit_type.split('(')[0].strip()}", zorder=10)
            self._style_ax(ax_main, show_xlabel=not show_resid)

        # Confidence band
        if self.show_ci_check.isChecked():
            sigma = np.std(residuals)
            ax_main.fill_between(x_fit, y_dense - sigma, y_dense + sigma,
                                 color=FIT_COLOR, alpha=0.12, label="±1σ band")

        # Equation text box
        if self.show_equation_check.isChecked():
            eq_lines = equation
            if len(eq_lines) > 55:
                eq_lines = eq_lines[:55] + "\n" + eq_lines[55:]
            info = f"{eq_lines}\nR² = {r_sq:.6f}"
            if scale_label:
                info += f"\n[{scale_label}]"
            ax_main.text(
                0.03, 0.97, info, transform=ax_main.transAxes,
                fontsize=9, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=WHITE,
                          edgecolor=DARK_BORDER, alpha=0.92),
                color=BLACK, fontfamily="monospace",
            )

        if show_resid:
            ax_main.tick_params(labelbottom=False)
            ax_resid.scatter(x_used, residuals, color=FIT_COLOR2, s=12, alpha=0.7, edgecolors="none")
            ax_resid.axhline(0, color="#999999", linewidth=0.8, linestyle="--")
            sigma = np.std(residuals)
            ax_resid.axhspan(-sigma, sigma, color=FIT_COLOR2, alpha=0.08)
            ax_resid.set_ylabel("Residuals", fontsize=10)
            x_label = self.xlabel_edit.text() or self.x_combo.currentText()
            ax_resid.set_xlabel(f"{label_log(transform_x)}({x_label})" if log_x else x_label)
            ax_resid.grid(True, alpha=0.2, linestyle="--")

        self.figure.tight_layout()
        self.canvas.draw()
        self.statusBar().showMessage(
            f"Fit: {fit_type}  |  R² = {r_sq:.6f}  |  RMS = {rms:.4g}"
            + (f"  |  scale: {fit_scale}" if fit_scale != "linear" else "")
        )

    def clear_plot(self):
        self.figure.clear()
        self.last_fit_result = None
        self.fit_results_text.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.5, 0.5, "Canvas cleared", transform=ax.transAxes,
                ha="center", va="center", fontsize=16, color="#999999", alpha=0.5)
        self.canvas.draw()
        self.statusBar().showMessage("Plot cleared")

    def export_plot(self):
        if not self.figure.axes:
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Plot", "plot",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg);;All (*)"
        )
        if not path:
            return

        # Determine the correct extension from the selected filter
        filter_ext_map = {
            "PNG": ".png",
            "PDF": ".pdf",
            "SVG": ".svg",
        }
        target_ext = None
        for key, ext in filter_ext_map.items():
            if key in selected_filter:
                target_ext = ext
                break

        # Replace or append extension to match the filter
        if target_ext:
            base, current_ext = os.path.splitext(path)
            if current_ext.lower() != target_ext:
                path = base + target_ext

        self.figure.savefig(path, dpi=200, bbox_inches="tight",
                            facecolor=self.figure.get_facecolor())
        self.statusBar().showMessage(f"Exported to {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(DARK_SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(DARK_SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(DARK_BG))
    app.setPalette(palette)

    window = ModernPlot()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
