"""Spinner Module. Shows loading."""

import itertools
import threading
import time
from collections.abc import Callable
from typing import TypeVar

import click

T = TypeVar("T")


def spinner(message: str, stop_event: threading.Event) -> None:
    """Spinner animation to show that the agent is working."""
    for char in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
        if stop_event.is_set():
            break
        click.echo(f"\r{char} {message}", nl=False)
        time.sleep(0.1)
    click.echo("\r✔ Done!          ")


def run_with_spinner[T](message: str, fn: Callable[[], T]) -> T:
    """Spinner runner."""
    stop_event = threading.Event()
    t = threading.Thread(target=spinner, args=(message, stop_event))
    t.start()
    try:
        result = fn()
    finally:
        stop_event.set()
        t.join()
    return result
