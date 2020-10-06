import pathlib
import os
import ipywidgets as widgets
import glob
import re
import sys
from IPython.display import display, clear_output
from canvasapi import Canvas
import subprocess
from typing import Union
import getpass
from .utils import _message_box


def _token_verif(course_code: int, api_url: str, token: Union[bool, str]):
    """Verify a connection to Canvas with the given params.

    Parameters
    ----------
    course_code : int
        Course code, get from canvas course url, e.g., 53659.
    api_url : str
        The base URL of the Canvas instance's API, e.g., "https://canvas.ubc.ca/"
    token : Union[bool, str]
        True if you have an environment variable "CANVAS_PAT". If you don't,
        set to False and enter token interactively. You can also pass your
        token directly as a string

    Returns
    -------
    canvasapi.course.Course
        Canvas course object
    """

    if token == True:
        api_key = os.environ.get("CANVAS_PAT")
        if api_key is None:
            raise NameError(
                "Sorry, I could not find a token 'CANVAS_PAT' in your environment variables.\nCheck your environment variables, or use 'submit(course_code, token_present=False)' to try enter your token interactively."
            )
        try:
            canvas = Canvas(api_url, api_key)
            course = canvas.get_course(course_code)
            return course
        except:
            print(
                "I found a token but could not access the given Canvas course.\nPerhaps you entered the wrong course code? Or your token is invalid?\nYou can also try to use 'submit(course_code, token=False)' to enter your token interactively."
            )
            raise
    elif isinstance(token, str):
        try:
            canvas = Canvas(api_url, token)
            course = canvas.get_course(course_code)
            return course
        except:
            print(
                "I could not access the given Canvas course with your token.\nPerhaps you entered the wrong course code? Or your token is invalid?"
            )
            raise

    else:
        print("Please paste your token here and then hit enter:")
        api_key = getpass.getpass()
        _message_box(" Token successfully entered - thanks!", color="green")
        print("")
        try:
            canvas = Canvas(api_url, api_key)
            course = canvas.get_course(course_code)
            return course
        except:
            print(
                "You entered a token but I could not access the given Canvas course.\nPerhaps you entered the wrong course code, the wrong token, or your token is invalid?"
            )
            raise


def _upload_assignment(file: str, assignment):
    """Submit file to Canvas assignment.

    Parameters
    ----------
    file : str
        Local file to upload.
    assignment : canvasapi.assignment.Assignment
        Canvas assignment to upload to.

    Returns
    -------
    canvasapi.assignment.Submission
        The submitted assignment.
    """
    try:
        file_id = assignment.upload_to_submission(file)[1]["id"]
        submission = assignment.submit(
            {"submission_type": "online_upload", "file_ids": [file_id]}
        )
        return submission
    except:
        raise CanvasError(
            f"Something went wrong and I could not submit your assignment.\nAre you using an instructor token? Instructors cannot submit assignments."
        )


def _text_submission(course, allowed_file_extensions: list = ["html"]):
    """Text-based assignment submission.

    Parameters
    ----------
    course : canvasapi.course.Course
        Canvas course object.
    allowed_file_extensions: list, optional
        List of allowed file extensions to choose from when submitting.
    """
    assignments = [
        (ass.name, ass.id)
        for ass in course.get_assignments()
        if "online_upload" in ass.submission_types
    ]
    assignment_names = [_[0] for _ in assignments]
    assignment_ids = [_[1] for _ in assignments]
    if not len(assignment_names):
        raise CanvasError(
            f"No assignments that accept file uploads are available for your course.\nPlease consult the course instructor about this issue."
        )
    _message_box("Entering text-based submission mode...", color="orange")
    print("Assignments available to submit to:")
    print(f" {assignment_names}")
    print("Enter the name of the assignment you wish to submit to:")
    ass = input().replace("'", "")  # replace single quotes if the user used them
    if not ass.lower() in [_.lower() for _ in assignment_names]:
        raise SelectionError(
            f"'{ass}' is not a valid assignment name. Please enter one of the following: {assignment_names}."
        )
    files = [file for ext in allowed_file_extensions for file in glob.glob("*." + ext)]
    if not len(files):
        raise OSError(
            f"No files with extensions {allowed_file_extensions} found.\nPlease add files to your local directory or change the kind of extensions allowed when running 'submit(course_code, ..., allowed_file_extensions = [])'."
        )
    print("")
    print("Files available to submit:")
    print(f" {files}")
    print(
        f"Enter the name of the file (including extension) you wish to submit to '{ass}':"
    )
    file = input().replace("'", "")
    if not file.lower() in [_.lower() for _ in files]:
        raise SelectionError(
            f"'{file}' is not a valid file name. Please enter one of the following: {files}."
        )
    print(f"")
    print(f"Submitting '{file}' to '{ass}'.")
    print("Please wait. This could take a minute.")
    ass_index = [_.lower() for _ in assignment_names].index(ass.lower())
    submission = _upload_assignment(
        file, course.get_assignment(assignment_ids[ass_index])
    )
    _message_box(
        "Successfully submitted!\n"
        "\n"
        "View your submission:\n"
        f"{submission.preview_url.split('?')[0]}"
    )


class _SubmitWidgets:
    """A convenience class for creating widgets.

    Parameters
    ----------
    course : canvasapi.course.Course
        Canvas course object
    allowed_file_extensions : list
        List of allowed file extensions, e.g., ["html", "csv"]
    widget_width : str, optional
        Display width of widgets in % or pixels, by default "25%"
    """

    def __init__(self, course, allowed_file_extensions, widget_width="25%"):
        """See 'help(_SubmitWidgets)'."""
        self.course = course
        self.widget_width = widget_width
        self.allowed_file_extensions = allowed_file_extensions

    def assignment_menu(self):
        assignments = [
            f"{ass.name} ({ass.id})"
            for ass in self.course.get_assignments()
            if "online_upload" in ass.submission_types
        ]
        if not len(assignments):
            raise CanvasError(
                f"No assignments that accept file uploads are available for your course.\nPlease consult the course instructor about this issue."
            )
        menu = widgets.Dropdown(
            options=assignments,
            layout=widgets.Layout(width=self.widget_width),
            value=assignments[-1],  # default to most recent assignment
            description="",
            disabled=False,
        )
        return menu

    def file_menu(self):
        files = [
            file
            for ext in self.allowed_file_extensions
            for file in glob.glob("*." + ext)
        ]
        if not len(files):
            raise OSError(
                f"No files with extensions {self.allowed_file_extensions} found.\nPlease add files to your local directory or change the kind of extensions allowed when running 'submit(course_code, ..., allowed_file_extensions = [])'."
            )

        menu = widgets.Dropdown(
            options=files,
            layout=widgets.Layout(width=self.widget_width),
            value=files[0],
            description="",
            disabled=False,
        )
        return menu

    def button(self, description="Select", style=""):
        button = widgets.Button(
            description=description,
            disabled=False,
            layout=widgets.Layout(width=self.widget_width),
            button_style=style,
            tooltip=f"Click to {description.lower()}.",
            icon="check",
        )
        return button

    @staticmethod
    def token(token_success):
        token = widgets.Valid(value=token_success, description="Token")
        return token

    @staticmethod
    def missing_token():
        missing_token = widgets.Text(
            value="", placeholder="Your token here", description="Token", disabled=False
        )
        return missing_token

    @staticmethod
    def output():
        return widgets.Output()


def submit(
    course_code: int,
    api_url: str = "https://canvas.ubc.ca/",
    allowed_file_extensions: list = ["html"],
    token: Union[bool, str] = True,
    widget_width: str = "25%",
    no_widgets: bool = False,
) -> None:
    """Interactive file submission to Canvas.

    Parameters
    ----------
    course_code : int
        Course code, get from canvas course url, e.g., 53659.
    api_url : str, optional
        The base URL of the Canvas instance's API, by default "https://canvas.ubc.ca/"
    allowed_file_extensions: list, optional
        List of allowed file extensions to choose from when submitting
    token : bool, optional
        True if you have an environment variable "CANVAS_PAT". If you don't,
        set to False and enter token interactively. You can also pass your
        token directly as a string, by default True
    widget_width: str, optional
        Width of the displayed widgets as a percentage of the output display, by default 25%
    no_widgets: bool, optional
        Specify True for a text-based submission without interactive widgets, by default False.
    """

    # Verify Token
    course = _token_verif(course_code, api_url, token)
    if not no_widgets:
        # Initialize widgets
        s = _SubmitWidgets(course, allowed_file_extensions, widget_width=widget_width)
        output = s.output()
        file_menu = s.file_menu()
        file_button = s.button("Select", style="success")
        ass_menu = s.assignment_menu()
        ass_button = s.button("Select", style="success")
        # Select assignment to submit to
        print("Select an assignment to submit to:")
        with output:
            display(ass_menu, ass_button)
        display(output)

        # Select assignment to submit
        def ass_click(ass_button):
            ass_button.disabled = True
            with output:
                print("\nSelect a file to submit:")
                display(file_menu, file_button)
            file_button.on_click(file_click)

        def file_click(file_button):
            file_button.disabled = True
            with output:
                print(f"")
                print(f"Submitting {file_menu.value} to {ass_menu.value}.")
                print("Please wait. This could take a minute.")
                print("")
            try:
                submission = _upload_assignment(
                    file_menu.value,
                    course.get_assignment(re.findall(r"\((\d+)\)", ass_menu.value)[-1]),
                )
                with output:
                    _message_box(
                        "Successfully submitted!\n"
                        "\n"
                        "View your submission:\n"
                        f"{submission.preview_url.split('?')[0]}"
                    )
            except CanvasError:
                with output:
                    _message_box(
                        "Something went wrong and I could not submit your assignment.\n"
                        "Are you using an instructor token? Instructors cannot submit assignments.\n"
                        "I'll print the traceback below.",
                        color="red",
                        border="=" * 73,
                    )
                    raise
                # print("Successfully Submitted!")
                # print(f"Preview here: {submission.preview_url.split('?')[0]}")

        ass_button.on_click(ass_click)
    else:
        _text_submission(course, allowed_file_extensions)


def convert_notebook(file_name: str, to_format: str = "html"):
    """Convert a .ipynb notebook file to another format using the nbconvert package.

    Parameters
    ----------
    file_name : str
        File to convert, e.g., "notebook.ipynb"
    to_format : str, optional
        Supported file format to convert to see https://nbconvert.readthedocs.io/en/latest/usage.html#supported-output-formats, by default "html"
    """

    outp = subprocess.run(
        ["jupyter", "nbconvert", "--to", to_format, file_name],
        capture_output=True,
    )

    if outp.returncode == 0:
        print("Notebook successfully converted! ")
    else:
        error = outp.stderr.decode("ascii")
        raise ConversionError(
            "Sorry I could not convert your notebook to {format}. You can try again, or convert your notebook manually. For example, in JupyterLab, File -> Export as... -> HTML. Here's the full traceback: {error}."
        )


class ConversionError(Exception):
    pass


class CanvasError(Exception):
    pass


class SelectionError(Exception):
    pass