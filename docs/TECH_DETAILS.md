# Technical details - Mouse Juggler

This document contains detailed technical information about the internal workings of Mouse Juggler.

## Architecture

Mouse Juggler is structured into several main components:

1. **Movement core**:

    - Implements the Bezier curve algorithm and movement logic
    - Functions: `bezier_curve()`, `smooth_trajectory()`, `human_move()`

2. **User interface**:

    - Tkinter-based graphical interface (when available)
    - Class: `MouseJugglerApp`

3. **Controllers**:

    - Movement loop control and thread management
    - Function: `movement_loop()`

4. **Key detection system**:
    - Quick stop using pynput for global key capture
    - Functions: `start_keyboard_listener()`

## Movement algorithms

### Bezier curves

Mouse Juggler uses quadratic Bezier curves to generate realistic mouse movements. The implemented formula is:

```
B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
```

Where:

-   P0 is the starting point (current mouse position)
-   P1 is the control point (randomly selected)
-   P2 is the end point (movement destination)
-   t varies from 0 to 1

This approach generates smooth and natural trajectories that don't follow straight lines, better simulating human movement.

### Control point selection

To generate realistic curves, the control point is selected in a direction perpendicular to the movement vector:

1. Calculate the movement vector: `vec = destination - origin`
2. Obtain a perpendicular vector: `perp = [-vec[1], vec[0]] / ||vec||`
3. The control point is placed at: `origin + vec/2 + perp * random(-dist/2, dist/2)`

This technique provides natural variability in the generated curves.

## Multithreading

The application uses multithreading to keep the user interface responsive while the mouse is moving:

1. The main thread runs the Tkinter graphical interface (or waits in console mode)
2. A secondary thread (`worker`) controls the mouse movement loop
3. Synchronization between threads is done using a `threading.Event` object

## Key detection

The key detection system uses the `pynput` library to capture keystrokes globally (outside the application):

1. A keyboard listener is created that runs in a separate thread
2. Any keystroke sets the stop event
3. The stop is propagated through the shared `stop_evt` object

## Cross-platform compatibility

The application is designed to work on:

-   Windows
-   macOS
-   Linux

This is achieved by using cross-platform libraries:

-   `pyautogui` for mouse control
-   `tkinter` for the graphical interface
-   `pynput` for key detection

## Error handling

The application implements error handling at various levels:

1. Detection of Tkinter availability with fallback to console mode
2. Exception capture in the movement loop
3. KeyboardInterrupt signal handling in console mode
