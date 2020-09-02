import pathlib
import os
import ipywidgets as widgets
import glob
import re
import sys
from IPython.display import display, clear_output
from canvasapi import Canvas


def _token_verif(course_code: int, api_url: str, token_present: bool):
    """Verify a connection to Canvas with the given params.

    Parameters
    ----------
    course_code : int
        Course code, get from canvas course url, e.g., 53659.
    api_url : str
        The base URL of the Canvas instance's API, e.g., "https://canvas.ubc.ca/"
    token_present : bool
        If you have an environment variable "CANVAS_API". If you don't,
        set to False and enter token interactively

    Returns
    -------
    canvasapi.course.Course
        Canvas course object
    """

    if token_present:
        api_key = os.environ.get("CANVAS_API")
        if api_key is None:
            raise NameError(
                "Sorry, I could not find a token 'CANVAS_API' in your environment variables. Check your environment variables, or use 'submit(course_code, token_present=False)' to try enter your token interactively."
            )
        try:
            canvas = Canvas(api_url, api_key)
            course = canvas.get_course(course_code)
            return course
        except:
            print(
                "I found a token but could not access the given Canvas course. Perhaps you entered the wrong course code? Or your token is invalid? You can also try to use 'submit(course_code, token_present=False)' to enter your token interactively."
            )
            raise
    else:
        print("Please paste your token here and then hit enter:")
        api_key = input()
        clear_output(wait=True)
        print("Token successfully entered - thanks!")
        print("")
        try:
            canvas = Canvas(api_url, api_key)
            course = canvas.get_course(course_code)
            return course
        except:
            print(
                "You entered a token but I still could not access the given Canvas course. Perhaps you entered the wrong course code? Or your token is invalid?"
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
        print(
            "Something went wrong and I could not submit your assignment. In case it's helpful, the error was:"
        )
        raise


class _SubmitWidgets:
    """A convenience class for creating widgets.

    Parameters
    ----------
    course : canvasapi.course.Course
        Canvas course object
    allowed_file_extensions : list
        List of allowed file extensions, e.g., ["html", "csv"]
    widget_width : str, optional
        Display width of widgets in % or pixels, by default "20%"
    """

    def __init__(self, course, allowed_file_extensions, widget_width="20%"):
        """See 'help(_SubmitWidgets)'."""
        self.course = course
        self.widget_width = widget_width
        self.allowed_file_extensions = allowed_file_extensions

    def assignment_menu(self):
        assignments = [
            f"{ass.name} ({ass.id})" for ass in self.course.get_assignments()
        ]
        menu = widgets.Dropdown(
            options=assignments,
            layout=widgets.Layout(width=self.widget_width),
            value=assignments[0],
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
    token_present: bool = True,
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
    token_present : bool, optional
        If you have an environment variable "CANVAS_API". If you don't,
        set to False and enter token interactively, by default True
    """

    # Verify Token
    course = _token_verif(course_code, api_url, token_present)
    # Initialize widgets
    s = _SubmitWidgets(course, allowed_file_extensions, widget_width="25%")
    output = s.output()
    file_menu = s.file_menu()
    file_button = s.button("Select", style="success")
    ass_menu = s.assignment_menu()
    ass_button = s.button("Select", style="success")
    # Select file to submit
    print("Select a file to submit:")
    with output:
        display(file_menu, file_button)
    display(output)
    # Select assinment to submit to then upload
    def file_click(file_button):
        file_button.disabled = True
        print("Select assignment to submit to:")
        with output:
            display(ass_menu, ass_button)
        ass_button.on_click(ass_click)

    def ass_click(ass_button):
        ass_button.disabled = True
        with output:
            print(f"Submitting {file_menu.value} to {ass_menu.value}.")
            print("Please wait. This could take a minute.")
            print("")
        submission = _upload_assignment(
            file_menu.value,
            course.get_assignment(re.findall(r"\((\d+)\)", ass_menu.value)[-1]),
        )
        with output:
            print("Successfully Submitted!")
            print(f"Preview here: {submission.preview_url.split('?')[0]}")

    file_button.on_click(file_click)