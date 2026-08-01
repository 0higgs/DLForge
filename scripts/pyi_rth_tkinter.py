"""Point bundled tkinter at DLForge's private Tcl/Tk libraries."""

import os
import sys
from pathlib import Path


bundle = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
os.environ["TCL_LIBRARY"] = str(bundle / "_tcl_data")
os.environ["TK_LIBRARY"] = str(bundle / "_tk_data")
