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

# Personal Dev Notes: 
# Change logic: do not look for /evdi in home, just clone it to /tmp/
# Same for DisplayLinkManager. 
# Will move playwright_scraper.py and executable over.
# This will require either including the playwright_scraper.py itself or the code inside as a function.
# Playwright drivers will have to be installed with this ENV:
# PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium
# 
# Python f-string example:  
# command = f'ls -l "{VAR}"'  
#
# Python subprocess.run output: $VAR.stdout
#
# Testing: 
# sudo -E $(which python) py_displaylink_synaptics_install.py

if os.getuid() != 0:
    print("Please run this script with `sudo`. Exiting.")
    sys.exit(1)

def dir_find(initSearchDir: Path, targetObj: str) -> list[Path]:
    return [d for d in Path(initSearchDir).rglob(targetObj) if d.is_dir()]

def file_find(initSearchDir: Path, targetObj: str) -> list[Path]:
    return [f for f in Path(initSearchDir).rglob(targetObj) if f.is_file()]

locUser: str | None = os.getenv('USER') if os.getenv('USER') else None
runitTest: subprocess.CompletedProcess[str] = subprocess.run("ps -p 1 -o comm=",
    shell=True, 
    capture_output=True, 
    text=True
)

initTmpDir: Path = Path("/tmp/")
evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
evdiGitPath: Path = Path("/tmp/evdi")
evdiTarPath: str = os.path.dirname(evdiGitPath)

installDec: bool | None = None
testDec: bool | None = None

def displaylink_install_check() -> bool:
    evdiTest: subprocess.CompletedProcess[str] = subprocess.run(f'lsmod | grep -Eio "evdi" | head -1', 
        shell=True, 
        capture_output=True, 
        text=True
    )
    displayInstallerTest: Path = Path("/usr/bin/displaylink-installer")
    isDisplayLinkInstalled: bool = True if (evdiTest.stdout and displayInstallerTest.is_file()) else False
    return isDisplayLinkInstalled

def uninstall_display_link() -> bool:
    dlTest = displaylink_install_check()
    if dlTest:
        print("uninstalling")
        dlUnSub: subprocess.CompletedProcess[str] = subprocess.run("displaylink-installer uninstall", 
            shell=True,
            capture_output=True,
            text=True
        )
        if dlUnSub.returncode != 0:
            return False
        else:
            return True
    else:
        return False

# Current DisplayLink Download: https://www.synaptics.com/sites/default/files/exe_files/2026-06/DisplayLink%20USB%20Graphics%20Software%20for%20Ubuntu6.3-EXE.zip
displayLinkFullNameUp: Path | None = None
displayLinkFileDir: Path | None = None
displayLinkInstallDir: Path | None = None

def download_displaylink() -> None:
    global displayLinkFullNameUp
    global displayLinkFileDir
    global displayLinkInstallDir

    py_playwright_scraper.py_scraper()
    displayLinkFullNameFind: list[Path] = file_find(initTmpDir, "DisplayLink*.zip")
    displayLinkFullName: Path | None = displayLinkFullNameFind[0] if displayLinkFullNameFind else None
    if not displayLinkFullName:
        sys.exit(1)
    else:
        displayLinkPath: Path = displayLinkFullName.parent
        displayLinkName: str = displayLinkFullName.name
        displayLinkNameFix: Path = displayLinkFullName.parent / displayLinkFullName.name.replace(" ", "_")
        displayLinkFullNameUp = displayLinkFullName.rename(displayLinkNameFix)
        displayLinkVer: List[str] = re.findall(r"\d+\.\d+", displayLinkFullNameUp.name)
        displayLinkTarget: str = f"displaylink_{displayLinkVer[0]}"
        displayLinkFileDir = displayLinkFullName.parent / displayLinkTarget
        displayLinkInstallDir = Path(f"/opt/{displayLinkTarget}")


def clean_files(evdiTp: str = evdiTarPath, 
    evdiGp: Path = evdiGitPath,
    dlfnUp: Path | None = displayLinkFullNameUp,
    dliDir: Path | None = displayLinkInstallDir, 
    sysEx: int = 0) -> None:

    if Path(f"{evdiTp}/evdi.tar.gz").is_file():
        with suppress(FileNotFoundError):
            os.remove(f"{evdiTp}/evdi.tar.gz")
    if evdiGp:
        with suppress(FileNotFoundError):
            shutil.rmtree(evdiGp)
    if dlfnUp:
        with suppress(FileNotFoundError):
            os.remove(dlfnUp)
    if dliDir and dliDir.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree(dliDir)
    sys.exit(sysEx)

def evdi_git_tag_util(evdiGp: Path = evdiGitPath,
    evdiTp: str = evdiTarPath,
    evdiGr: str = evdiRepo,
    initTd: Path = initTmpDir) -> None:

    evdiGitMain: str
    evdiGitTag: str

    if evdiGp.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree(evdiGp)
        with suppress(FileNotFoundError):
            os.remove(f"{initTd}evdi.tar.gz")

    try:   
        Repo.clone_from(evdiGr, evdiGp)
    except GitCommandError:
        clean_files(sysEx=1)

    os.chdir(evdiGp)
    localEvdiRepo: git.repo.base.Repo = git.Repo(evdiGp)
    localEvdiOrigin: git.remote.Remote = localEvdiRepo.remotes.origin
    localEvdiOrigin.pull()
    evdiGitMainFind: subprocess.CompletedProcess[str] = subprocess.run("git rev-parse --abbrev-ref origin/HEAD | cut -d/ -f2", 
        shell=True, 
        capture_output=True,
        text=True
    )

    if not evdiGitMainFind:
        clean_files(sysEx=1)
    else:
        evdiGitMain = evdiGitMainFind.stdout.strip()

    evdiList: List[TagReference] = sorted(localEvdiRepo.tags, 
        key=lambda t: t.commit.committed_date, 
        reverse=True
    )

    if not evdiList:
        clean_files(sysEx=1)

    # Create Dynamic menu for Textualize
    # for tag in evdiList:
    #     print(tag.name, tag.commit.committed_datetime)

    # latest tag - placeholder
    print(f"evdiList: {evdiList[0]}")
    evdiGitTag = evdiList[0]

    localEvdiOrigin.fetch(tags=True)
    localEvdiRepo.git.checkout("-b", evdiGitTag)

    with tarfile.open(f"{evdiTp}/evdi.tar.gz", "w:gz") as tarFile:
        tarFile.add(evdiGp, arcname=".")

    localEvdiRepo.git.checkout(evdiGitMain)
    localEvdiRepo.delete_head(evdiGitTag)

    
def unzip_displaylink(dlfnUp: Path | None = displayLinkFullNameUp,
    dlfDir: Path | None = displayLinkFileDir) -> None:
    if dlfnUp and dlfDir:
        with zipfile.ZipFile(dlfnUp, 'r') as zipRef:
            zipRef.extractall(dlfDir)


def install_dir_rename(dlfDir: Path | None = displayLinkFileDir,
    dliDir: Path | None = displayLinkInstallDir) -> None:
    if dlfDir and dliDir:
        shutil.move(dlfDir, dliDir)

def extract_displaylink_firmware(dliDir: Path | None = displayLinkInstallDir,
    evdiTp: str = evdiTarPath) -> None:
    if not dliDir:
        clean_files(sysEx=1)
    else:
        os.chdir(dliDir)
        runFileFind: list[Path] = file_find(dliDir, "*.run")
        runFile: Path | None = runFileFind[0] if runFileFind else None
        if runFile is None:
            clean_files(sysEx=1)
        else:
            subprocess.run(["chmod", "+x", runFile], check=True)
            try:
                subprocess.run([runFile, "--noexec", "--keep"], check=True)
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    os.chdir("/opt")
                    clean_files(sysEx=1)

            extractDirFind: list[Path] = dir_find(dliDir, "displaylink-*")
            extractDir: Path | None = extractDirFind[0] if extractDirFind else None
            if extractDir is None:
                clean_files(sysEx=1)
            else:
                os.chdir(str(extractDir))
                os.remove("evdi.tar.gz")
                shutil.move(Path(f"{evdiTp}/evdi.tar.gz"), extractDir)
                subprocess.run(["chmod", "+x", f"{extractDir}/displaylink-installer.sh"], check=True)
                subprocess.run(["./displaylink-installer.sh", "noreboot"], check=True)


    # Menu to capture evdi decision, then do the remaining operations
    #
    # download_displaylink()
    # evdi_git_tag_util()
    # unzip_displaylink()
    # install_dir_rename()
    # extract_displaylink_firmware()
    # clean_files()


MODAL_MESSAGE = """
[bold]>>> Warning:[/bold] DisplayLink Firmware is already installed. Proceed?

::: Navigate using `Tab`
"""

UNINSTALL_MESSAGE = """
[bold]>>> Uninstall the DisplayLink and EVDI Firmwares?[/bold]

::: Select [bold]'Yes'[/bold] to uninstall
::: Select [bold]'No'[/bold] to exit the app


[bold]Note:[/bold] 

An uninstall will require a reboot to fully remove the EVDI software driver and this installer will have to be re-run.
"""

# Installed Warning Modal
class InstallModal(ModalScreen[bool]):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="installDialog"):
            yield Static(MODAL_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield Button("No", id="noBtn", classes="dialogQbtn")
                yield Button("Yes", id="instBtn", classes="dialogQbtn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "instBtn":
            self.dismiss(True)
        else:
            self.dismiss(False)


class IntroContainer(Container):
    CSS_PATH = "styles.tcss"

    # Container for DisplayLink/Evdi Events
    # Uninstall Logic if True, else download Displaylink and EVDI
    def compose(self) -> ComposeResult:
        yield Label(f"::: Hello.", id="installDec")


class UninstallDialogScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(self, uninistallDisplay, **kwargs) -> None:
        self.uninistallDisplay = uninistallDisplay
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(UNINSTALL_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield Button("Yes", id="yesUnBtn", classes="dialogUnbtn")
                yield Button("No", id="noUnBtn", classes="dialogUnbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesUnBtn":
            # Once complete, exit callback with either 'call_from_thread' with python `thread` or @work decorator
            if False:
                self.uninistallDisplay()
            self.app.push_screen(UninstallIndicatorScreen(uninistallDisplayInd=self.uninistallDisplay))
        else:
            self.app.exit()

class UninstallIndicatorScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(self, uninistallDisplayInd, **kwargs) -> None:
        self.uninistallDisplayInd = uninistallDisplayInd
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstalling Synaptics DisplayLink Driver and the EVDI software driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    @work(thread=True)
    def exec_uninistallDisplayInd(self) -> None:
        # self.uninistallDisplayInd()
        time.sleep(1.5)

        self.call_from_thread(self.app.push_screen(UninstallCompleteScreen()))

    exec_uninistallDisplayInd()


class UninstallCompleteScreen(Screen):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstalling Synaptics DisplayLink Driver and the EVDI software driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")


class AppScreen(Screen):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstallation Complete. Restart?")
            with Grid(id="horizontalInstBtn"):
                yield Button("Yes", id="yesReBtn", classes="dialogUnbtn")
                yield Button("No", id="noReBtn", classes="dialogUnbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesReBtn":
            # Restart Computer
            self.app.exit()
        else:
            self.app.exit()


class DisplayLinkInstaller(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the DisplayLink Installer")
    ]

    CSS_PATH = "styles.tcss"

    def __init__(self, displayLinkInstallCheck, uninistallDisp, **kwargs) -> None:
        self.displayLinkInstallCheck = displayLinkInstallCheck
        self.uninistallDisp = uninistallDisp
        super().__init__(**kwargs)

    modal_result = reactive[bool | None](None)

    def on_mount(self) -> None:
        self.theme = "nord"

    def on_ready(self) -> None:
        self.push_screen(AppScreen())
        if self.displayLinkInstallCheck:
            self.push_screen(InstallModal(), self.handle_modal_result)

    def handle_modal_result(self, result: bool | None) -> None:
        self.modal_result = result

    def watch_modal_result(self, old_value: bool | None, new_value: bool | None) -> None:
        if new_value is not None:
            # Cool Feature. Keep for notes for now.
            # status_label = self.screen.query_one("#installDec", Label)
            # status_label.update(f"::: Hello: {new_value}")
            if not new_value:
                self.exit()
            else:
                self.push_screen(UninstallDialogScreen(uninistallDisplay=self.uninistallDisp))



    # def compose(self) -> ComposeResult:
        # yield Header()
        # yield Label(f"::: {self.displayLinkInstallCheck}")
        # yield Button("Start", id="start", variant="primary") 
        # yield Button("No", id="no", variant="error")
        # yield Footer()

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     self.exit(event.button.id)


if __name__ == "__main__":
    app = DisplayLinkInstaller(displayLinkInstallCheck=displaylink_install_check(),
            uninistallDisp=uninstall_display_link
            )
    # reply = app.run()
    # print(f"reply: {reply}")
    app.run()
