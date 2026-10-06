import os
import sys
import subprocess
import shutil
import git
import tarfile
import zipfile
import re
import py_playwright_scraper
import time
from contextlib import suppress
from pathlib import Path
from typing import List
from git import Repo
from git import TagReference
from git.exc import GitCommandError
from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll, Grid
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Header, Footer, RichLog, Welcome, Label, Button
from textual.widgets import Placeholder, Static, LoadingIndicator
from typing import Optional