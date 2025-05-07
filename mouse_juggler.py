#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mouse Juggler - Mouse movement automation with natural patterns.

This script provides a tool to automatically move the mouse with movement
patterns that simulate human behavior using Bezier curves.
Includes both a GUI mode (Tkinter) and a console mode.

Author: Arturo
License: MIT
"""

# Version information (used by setup.py and release scripts)
VERSION = "1.0.0"

import logging
import random
import sys
import threading
import time
from itertools import islice

import numpy as np
import pyautogui as pag

# --------------------------------- utilities ---------------------------------
def pairwise(iterable):
    "equivalent to itertools.pairwise (Python 3.10+) for 3.8+"
    it = iter(iterable)
    prev = next(it, None)
    for item in it:
        yield prev, item
        prev = item

def bezier_curve(start, control, end, n):
    t = np.linspace(0, 1, n)[:, None]        # (n,1) for broadcasting
    return (((1 - t) ** 2) * start
            + 2 * (1 - t) * t * control
            + (t ** 2) * end).astype(int)

def smooth_trajectory(origin, destination, steps):
    vec = np.array(destination) - np.array(origin)
    dist = np.linalg.norm(vec)
    if dist == 0:
        return [np.array(origin)]
    perp = np.array([-vec[1], vec[0]]) / dist
    control = (np.array(origin)
               + vec / 2
               + perp * random.uniform(-dist / 2, dist / 2)).astype(int)
    return bezier_curve(np.array(origin), control, np.array(destination), steps)

def human_move(origin, destination, speed_range, steps_range, stop_evt=None):
    points = smooth_trajectory(origin, destination,
                              random.randint(*steps_range))
    total = sum(np.linalg.norm(b - a) for a, b in pairwise(points))
    speed = random.uniform(*speed_range)               # px / s
    pause = total / speed / max(len(points) - 1, 1)
    for p in points:
        # Check if we should stop the movement
        if stop_evt and stop_evt.is_set():
            break
        pag.moveTo(int(p[0]), int(p[1]))
        # Small pauses to allow cancellation
        if pause > 0.1 and stop_evt:
            segments = int(pause / 0.1)
            for _ in range(segments):
                if stop_evt.is_set():
                    return
                time.sleep(0.1)
            time.sleep(pause % 0.1 + random.uniform(0, pause * .1))
        else:
            time.sleep(pause + random.uniform(0, pause * .1))

# --------------------------- default configuration -------------------------
CFG_DEFAULT = dict(
    dx=(80, 300),
    dy=(80, 300),
    pause=(1.5, 7),
    steps=(20, 50),
    vel=(200, 800),
)

def movement_loop(stop_evt, cfg):
    """Thread that moves the mouse until stop_evt is active."""
    logging.info("Movement loop started.")
    while not stop_evt.is_set():
        x0, y0 = pag.position()
        dx = random.randint(*cfg['dx']) * random.choice((-1, 1))
        dy = random.randint(*cfg['dy']) * random.choice((-1, 1))
        w, h = pag.size()
        x1 = max(1, min(w - 2, x0 + dx))
        y1 = max(1, min(h - 2, y0 + dy))
        human_move((x0, y0), (x1, y1),
                  cfg['vel'], cfg['steps'], stop_evt)
        # Check if we should finish before the pause
        if stop_evt.is_set():
            break
        # Segment the pause to be able to respond faster
        total_pause = random.uniform(*cfg['pause'])
        for _ in range(int(total_pause)):
            if stop_evt.is_set():
                break
            time.sleep(1)
        if not stop_evt.is_set():
            time.sleep(total_pause % 1)
    logging.info("Movement loop stopped.")

# ----------------------------- keyboard listener -----------------------------
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logging.warning("pynput not found; global keyboard stop disabled.")

def start_keyboard_listener(stop_evt, on_first_key=None):
    if not KEYBOARD_AVAILABLE:
        return None

    def _on_press(key):
        if not stop_evt.is_set():
            stop_evt.set()
            logging.info("Stop requested by key press: %s", key)
            if on_first_key and _app_instance:
                # Schedule safe call in UI main thread
                _app_instance.after(100, on_first_key)
            elif on_first_key:
                on_first_key()
        # stop on first event
        return False

    listener = keyboard.Listener(on_press=_on_press, suppress=False)
    listener.start()
    return listener

# -------------------------------- GUI (Tkinter) -------------------------------
GUI_AVAILABLE = False
GUI_ERROR = None
_app_instance = None      # To update UI from other threads

try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except Exception as e:
    GUI_ERROR = e
    GUI_AVAILABLE = False
    logging.warning("GUI not available (%s). Console mode will be used.", e)

class MouseJugglerApp(tk.Tk):
    """Blue interface with controls and dynamic status."""
    COLOR_BG = "#cbe2ff"
    COLOR_FG = "#043b74"

    def __init__(self):
        super().__init__()
        global _app_instance
        _app_instance = self

        self.title("Mouse Juggler")
        self.resizable(False, False)
        self.configure(bg=self.COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ttk styles
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=self.COLOR_BG, foreground=self.COLOR_FG)
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))

        # Tk variables for parameters
        self.v_dx_min   = tk.IntVar(value=80)
        self.v_dx_max   = tk.IntVar(value=300)
        self.v_dy_min   = tk.IntVar(value=80)
        self.v_dy_max   = tk.IntVar(value=300)
        self.v_pause_min = tk.DoubleVar(value=1.5)
        self.v_pause_max = tk.DoubleVar(value=7)
        self.v_steps_min = tk.IntVar(value=20)
        self.v_steps_max = tk.IntVar(value=50)
        self.v_vel_min   = tk.DoubleVar(value=200)
        self.v_vel_max   = tk.DoubleVar(value=800)

        # Status (to show stops)
        self.status = tk.StringVar(value="Inactive")

        self._create_widgets()

        # Thread and stop signal
        self.stop_event = threading.Event()
        self.worker = None
        self.keyboard_listener = None

    def _create_widgets(self):
        frame = ttk.Frame(self, padding=10)
        frame.grid()

        # Optional image
        try:
            self.image = tk.PhotoImage(file="logo.png")      # Change the file name
            ttk.Label(frame, image=self.image).grid(columnspan=2, pady=(0, 8))
        except Exception:
            pass  # Ignore if the image doesn't exist

        # ---- parameter helper ----
        def spin(frame, txt, var, mn, mx, inc):
            ttk.Label(frame, text=txt).grid(sticky="w")
            sb = ttk.Spinbox(frame, textvariable=var, from_=mn, to=mx,
                             increment=inc, width=8, justify="right")
            sb.grid()

        # Control columns
        col1 = ttk.LabelFrame(frame, text="Displacement (px)")
        col1.grid(row=1, column=0, padx=5, pady=5)
        spin(col1, "ΔX min", self.v_dx_min, 1, 800, 10)
        spin(col1, "ΔX max", self.v_dx_max, 1, 1600, 10)
        spin(col1, "ΔY min", self.v_dy_min, 1, 800, 10)
        spin(col1, "ΔY max", self.v_dy_max, 1, 1600, 10)

        col2 = ttk.LabelFrame(frame, text="Speed/Pause/Curve")
        col2.grid(row=1, column=1, padx=5, pady=5)
        spin(col2, "Speed min (px/s)", self.v_vel_min, 10, 3000, 50)
        spin(col2, "Speed max", self.v_vel_max, 20, 4000, 50)
        spin(col2, "Pause min (s)", self.v_pause_min, .1, 20, .1)
        spin(col2, "Pause max", self.v_pause_max, .1, 60, .1)
        spin(col2, "Steps min", self.v_steps_min, 5, 100, 1)
        spin(col2, "Steps max", self.v_steps_max, 5, 150, 1)

        # Buttons and status
        btns = ttk.Frame(frame)
        btns.grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_start = ttk.Button(btns, text="Start", command=self.start)
        self.btn_stop  = ttk.Button(btns, text="Stop", command=self.stop, state="disabled")
        self.btn_start.grid(row=0, column=0, padx=4)
        self.btn_stop.grid(row=0, column=1, padx=4)

        ttk.Label(frame, textvariable=self.status,
                  font=("Segoe UI", 10, "italic")).grid(columnspan=2, pady=(4, 0))

    # ---------------- movement control ----------------
    def _current_cfg(self):
        return dict(
            dx=(self.v_dx_min.get(), self.v_dx_max.get()),
            dy=(self.v_dy_min.get(), self.v_dy_max.get()),
            pause=(self.v_pause_min.get(), self.v_pause_max.get()),
            steps=(self.v_steps_min.get(), self.v_steps_max.get()),
            vel=(self.v_vel_min.get(), self.v_vel_max.get()),
        )

    def _update_status(self, txt):
        self.status.set(txt)

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        self.stop_event.clear()
        
        # Create a new keyboard listener each time we start
        self.keyboard_listener = start_keyboard_listener(
            self.stop_event,
            on_first_key=self.key_stop_handler
        )
        
        self.worker = threading.Thread(target=movement_loop,
                                       args=(self.stop_event, self._current_cfg()),
                                       daemon=True)
        self.worker.start()
        self._update_status("Moving…")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

    def stop(self):
        self.stop_event.set()
        self._update_status("Stopped")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def on_close(self):
        self.stop()
        self.destroy()

    def key_stop_handler(self):
        self._update_status("Stopped by key")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

# ------------------------------ console mode ----------------------------------
def run_console():
    """Run the movement without GUI."""
    logging.info("Running in console mode.")
    stop_evt = threading.Event()
    start_keyboard_listener(stop_evt,
                           on_first_key=lambda: print("Stopped by key."))
    try:
        movement_loop(stop_evt, CFG_DEFAULT)
    except KeyboardInterrupt:
        stop_evt.set()
    print("End.")

# ---------------------------------- main --------------------------------------
def main():
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s",
                        level=logging.INFO)

    if GUI_AVAILABLE:
        try:
            app = MouseJugglerApp()
            app.mainloop()
        except Exception as e:
            logging.exception("GUI failed (%s). Switching to console mode.", e)
            run_console()
    else:
        logging.info("GUI not available (%s).", GUI_ERROR or "no Tk")
        run_console()

if __name__ == "__main__":
    main()