import os
import re
import sys
import json
import time
import subprocess
import threading
import tkinter as tk


import customtkinter as ctk
import pytesseract
import queue
from PIL import Image, ImageEnhance, ImageGrab, ImageOps, ImageDraw, ImageTk
from tkinter import PhotoImage

from avalon.i18n import Translator
from avalon.paths import ASSETS_DIR, BASE_DIR, DATA_DIR, LOCALES_DIR, MAPS_DIR
from avalon.hotkeys import bind_ocr_hotkey
from avalon.maps_store import (
    best_match,
    filter_maps,
    find_by_name,
    first_search_hit,
    load_maps,
)
from avalon.ocr import check_tesseract, read_name_near_cursor
from avalon.info_panel import InfoPanel
from avalon.left_panel import LeftPanel
from avalon.map_view import MapView
from avalon.app import AvalonMapViewer
