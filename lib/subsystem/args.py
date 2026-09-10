# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Typed command-line arguments for launcher-managed subsystems.

A subsystem describes its flags by subclassing SubsystemArgs and adding fields; the base
builds the argparse parser from those fields and hands back a populated instance. This
replaces the older add_args(parser) hook, whose result was an untyped argparse.Namespace.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import argparse
from dataclasses import MISSING, dataclass, field, fields
from typing import Any, Union, get_args, get_origin, get_type_hints

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def arg(default: Any, help_text: str, **argparse_kwargs: Any) -> Any:
    """Declare one command-line flag as a dataclass field.

    Every flag needs help text, so it is positional rather than buried in a metadata dict.
    Anything else argparse understands - nargs, choices, metavar - passes through as keyword
    arguments and is forwarded verbatim.

    Args:
        default (Any): Value when the flag is absent
        help_text (str): Help string, shown by --help
        **argparse_kwargs (Any): Extra add_argument() keyword arguments, forwarded as-is

    Returns:
        Any: A dataclass field. Typed Any so it satisfies whatever the field is annotated as.
    """

    # pylint only recognises field() written directly in a dataclass body. It is legal to
    # return one from a helper - the dataclass decorator sees the same object either way.
    return field(default=default, metadata={"help": help_text, **argparse_kwargs})  # pylint: disable=invalid-field-call

def _unwrap_optional(annotation: Any) -> Any:
    """Reduce Optional[X] to X, leaving anything else alone.

    Args:
        annotation (Any): Resolved type annotation

    Returns:
        Any: The annotation with a NoneType union member stripped
    """

    if get_origin(annotation) is Union:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation

def add_dataclass_args(parser: argparse.ArgumentParser, args_cls: type["SubsystemArgs"]) -> None:
    """Add one argparse flag per field of args_cls, in declaration order.

    Field name maps to flag name - replay_server becomes --replay-server, and argparse's dest
    turns it back into replay_server, so the parsed namespace maps straight onto the fields.

    Args:
        parser (argparse.ArgumentParser): Parser to populate
        args_cls (type[SubsystemArgs]): Dataclass describing the flags

    Raises:
        TypeError: A field is unusable as a flag - see the individual messages
    """

    # Resolves string annotations, which `from __future__ import annotations` or a quoted hint
    # would otherwise leave as text.
    hints = get_type_hints(args_cls)

    for f in fields(args_cls):
        if f.default is MISSING:
            raise TypeError(
                f"{args_cls.__name__}.{f.name} has no default. Every subsystem flag is optional - "
                f"the launcher only passes the ones it needs - so give it the value that applies "
                f"when the flag is absent.")

        flag = "--" + f.name.replace("_", "-")
        kwargs = dict(f.metadata)

        if _unwrap_optional(hints[f.name]) is bool:
            # store_true is the only bool form in use, and it cannot express "on unless the
            # flag is passed" - the flag would be unable to turn the value off. Reject that
            # here rather than shipping a flag that silently does nothing.
            if f.default:
                raise TypeError(
                    f"{args_cls.__name__}.{f.name} is a bool defaulting to True, which no flag "
                    f"could switch off. Invert the name and the default instead.")
            parser.add_argument(flag, action="store_true", **kwargs)
        else:
            parser.add_argument(flag, type=_unwrap_optional(hints[f.name]),
                                default=f.default, **kwargs)

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(frozen=True)
class SubsystemArgs:
    """The flags every launcher-managed subsystem accepts.

    Subclass to add more, and point the subsystem's ARGS class variable at the subclass:

        @dataclass(frozen=True)
        class McpArgs(SubsystemArgs):
            managed: bool = arg(False, "Indicates if process is managed by parent")

    Frozen because these are the invocation, not mutable state - a subsystem that wants to
    vary something at run time has settings for that.

    Every field must carry a default, which dataclass inheritance requires anyway once a base
    field has one. add_dataclass_args() says so explicitly rather than letting the failure
    surface as dataclass's own "non-default argument follows default argument".
    """

    config_file: str = arg("png_config.json", "Configuration file name (optional)", nargs="?")
    debug: bool = arg(False, "Enable debug mode")
    smoke_test: bool = arg(False, "Construct the subsystem, then exit without running it")
