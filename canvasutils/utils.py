from textwrap import dedent

endc = "\033[0m"
bcolors = dict(
    blue="\033[94m",
    green="\033[92m",
    orange="\033[93m",
    red="\033[91m",
    bold="\033[1m",
    underline="\033[4m",
)


def _color_message(msg, style):
    return bcolors[style] + msg + endc


def _message_box(msg, color="green", border="=" * 38, doprint=True, print_func=print):
    # Prepare the message so the indentation is the same as the box
    msg = dedent(msg)

    # Color and create the box
    border_colored = _color_message(border, color)
    box = """
    {border_colored}
    {msg}
    {border_colored}
    """
    box = dedent(box).format(msg=msg, border_colored=border_colored)
    if doprint is True:
        print_func(box)
    return box
