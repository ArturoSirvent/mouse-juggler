# Contributing to Mouse Juggler

Thank you for your interest in contributing to Mouse Juggler! This document provides guidelines for contributing to the project.

## Contribution process

1. **Fork the repository**

    - Fork the repository to your own GitHub account.

2. **Clone your fork**

    ```bash
    git clone https://github.com/YOUR-USERNAME/mouse-juggler.git
    cd mouse-juggler
    ```

3. **Create a branch for your feature**

    ```bash
    git checkout -b feature/your-feature
    ```

4. **Make your changes**

    - Make sure to follow the code conventions described below
    - Add or update tests as necessary
    - Update documentation if applicable

5. **Test your changes**

    ```bash
    python -m unittest discover tests
    ```

6. **Commit and push**

    ```bash
    git commit -am "Clear description of the change"
    git push origin feature/your-feature
    ```

7. **Create a Pull Request**
    - Provide a clear description of the changes made
    - Mention any related issues using #issue-number

## Code conventions

-   Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style
-   Use descriptive names for variables and functions
-   Write docstrings for functions and classes following [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
-   Keep lines to a maximum of 88 characters
-   Use spaces instead of tabs

## Reporting bugs

If you find a bug, please create an issue on GitHub including:

-   Clear description of the problem
-   Steps to reproduce the bug
-   Information about your environment (operating system, Python version, etc.)
-   Screenshots if relevant

## Requesting new features

To request a new feature:

1. First verify that the feature hasn't been previously requested
2. Create an issue describing the feature and its use case
3. Explain how it would benefit the project and its users

## Questions or concerns

If you have questions about the code or the project in general, open an issue with the "question" label or contact the maintainers directly.

---

Your contribution is appreciated and helps improve the project for everyone!
