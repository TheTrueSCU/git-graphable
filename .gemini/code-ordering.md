# Python Code Ordering Guidelines

Please ensure all Python files adhere to the following structure and ordering conventions:

## Module-Level Ordering

The sequence of elements at the top level of a Python module should be:

1.  **Module-level Docstrings:** A concise description of the file's purpose.
    ```python
    """
    This module provides utility functions for path manipulation.
    """
    ```
2.  **Imports:** Grouped in a specific order:
    *   **Standard Library Imports:** (e.g., `os`, `sys`, `datetime`)
        ```python
        import os
        import sys
        from pathlib import Path
        ```
    *   **Third-Party Library Imports:** (e.g., `requests`, `numpy`)
        ```python
        import requests
        import numpy as np
        ```
    *   **Local Application Imports:** Imports from your project's own modules.
        ```python
        from . import utils
        from ..core import models
        ```
3.  **Module-level Globals/Constants:** Variables declared at the module level, typically in `ALL_CAPS`.
    ```python
    DEFAULT_TIMEOUT = 30
    CONFIG_PATH = "/etc/myapp/config.ini"
    ```
4.  **Classes and Functions:**
    *   Higher-level definitions should usually precede lower-level helper functions or classes.
    *   For classes, follow the "Class Internal Ordering" below.
    *   For functions, utility functions often come before main operational functions.
5.  **Main Entry Point:** The `if __name__ == "__main__":` block, placed at the very bottom.

## Class Internal Ordering

Within a class, elements should be ordered logically and by visibility:

1.  **Class Attributes:** Constants or shared state variables belonging to the class.
    ```python
    class MyClass:
        CLASS_CONSTANT = 100
    ```
2.  **`__init__` Method:** The constructor.
    ```python
    def __init__(self, value):
        self.value = value
    ```
3.  **Magic Methods:** Other dunder methods (e.g., `__str__`, `__repr__`, `__eq__`).
    ```python
    def __str__(self):
        return f"MyClass({self.value})"
    ```
4.  **Public Methods:** The primary ways other code interacts with your class.
    ```python
    def public_method(self):
        # ...
    ```
5.  **Protected and Private Methods:** Implementation details prefixed with `_` or `__` (that aren't magic methods).
    ```python
    def _helper_method(self):
        # ...
    ```
6.  **Static and Class Methods:** Often placed at the end, or grouped near related public methods if they act as factory methods.
    ```python
    @staticmethod
    def static_method():
        # ...

    @classmethod
    def class_method(cls):
        # ...
    ```

## General Layout Principles

*   **Vertical Distance:** Keep related methods close together. Use two blank lines between top-level definitions (module docstring, imports, classes, functions) and one blank line between methods within a class.
*   **Step-Down Rule:** Place a "caller" method immediately above the "callee" method it uses. (This is more of a guideline for readability than a strict ordering rule.)
