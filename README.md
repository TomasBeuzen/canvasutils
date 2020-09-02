# CanvasUtils

Utilities for interacting with Canvas using Python and the canvasapi.

## Installation

```bash
pip install canvasutils
```

## Features

- Submit files to Canvas from within a Jupyter notebook.
- Create assignments (coming)
- Create assignment rubrics (coming)

## Dependencies

See the file [pyproject.toml](pyproject.toml), `[tool.poetry.dependencies]`.

## Usage

### Assignment Submission in Jupyter

The submit module is made to be used within a Jupyter notebook (.ipynb file):

![](docs/img/assignment_submit.gif)

```python
api_url = "https://canvas.instructure.com/"
course_code = 123456

from canvasutils.submit import submit
submit(course_code, api_url=api_url, token_present=False)  # token present false allows you to enter token interactively.
```

## Contributors

Contributions are welcomed and recognized. You can see a list of contributors in the [contributors tab](https://github.com/TomasBeuzen/canvasutils/graphs/contributors).

### Credits

This package was originally based on [this repository](https://github.com/eagubsi/JupyterCanvasSubmit) created by Emily Gubski and Steven Wolfram.
