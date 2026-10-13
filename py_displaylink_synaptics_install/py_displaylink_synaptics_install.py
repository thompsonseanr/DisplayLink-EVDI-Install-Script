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
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import List
from git import Repo
from git import TagObject
from git import TagReference
from git.exc import GitCommandError
from packaging.version import parse
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Container, Horizontal, VerticalScroll, Grid
from textual.events import Print, Key
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Header, Footer, RichLog, Welcome, Label, Button
from textual.widgets import Placeholder, Static, LoadingIndicator, ListView, ListItem

# Personal Dev Notes:
# Write error catching and file removal scripts on failures
# Playwright drivers will have to be installed with this ENV:
# PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium

if os.getuid() != 0:
    print("Please run this script with `sudo`. Exiting.")
    sys.exit(1)


def dir_find(initSearchDir: Path, targetObj: str) -> list[Path]:
    return [d for d in Path(initSearchDir).rglob(targetObj) if d.is_dir()]

def file_find(initSearchDir: Path, targetObj: str) -> list[Path]:
    return [f for f in Path(initSearchDir).rglob(targetObj) if f.is_file()]


class DispLink:

    initTmpDir: Path = Path("/tmp/")
    evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
    evdiGitPath: Path = Path("/tmp/evdi")
    evdiTarPath: str = os.path.dirname(evdiGitPath)
    evdiOrigin: git.remote.Remote
    evdiList: List[TagReference]
    localEvdiRepo: git.repo.base.Repo
    displayLinkFullNameUp: Path | None = None
    displayLinkFileDir: Path | None = None
    displayLinkInstallDir: Path | None = None

    @staticmethod
    def runit_test() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            f"ps -p 1 -o comm=",
            shell=True,
            capture_output=True, 
            text=True
        )

    @staticmethod
    def displaylink_install_check() -> bool:
        evdiTest: subprocess.CompletedProcess[str] = subprocess.run(
            f'lsmod | grep -Eio "evdi" | head -1', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        displayInstallerTest: Path = Path("/usr/bin/displaylink-installer")
        isDisplayLinkInstalled: bool = True if (evdiTest.stdout and displayInstallerTest.is_file()) else False
        return isDisplayLinkInstalled

    @staticmethod
    def uninstall_display_link() -> Iterator[str]:
        with subprocess.Popen(
            ["displaylink-installer", "uninstall"], 
            shell=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1
            ) as unProc:
            assert unProc.stdout is not None
            for line in unProc.stdout:
                yield line.rstrip()
        
        unProc.wait()
        if unProc.returncode != 0:
            yield f"[red]DisplayLink uninstallation failed. Exit code: {unProc.returncode}[/]"

    @classmethod
    def download_displaylink(cls) -> None:
        displayLinkFullNameFindArt: list[Path] = file_find(cls.initTmpDir, "DisplayLink*.zip")
        if displayLinkFullNameFindArt:
            for fd in displayLinkFullNameFindArt:
                if fd and fd.is_file():
                    os.remove(fd)

        py_playwright_scraper.py_scraper()

        displayLinkFullNameFind: list[Path] = file_find(cls.initTmpDir, "DisplayLink*.zip")
        displayLinkFullName: Path | None = displayLinkFullNameFind[0] if displayLinkFullNameFind else None
        if not displayLinkFullName:
            sys.exit(1)
        else:
            displayLinkPath: Path = displayLinkFullName.parent
            displayLinkName: str = displayLinkFullName.name
            displayLinkNameFix: Path = displayLinkFullName.parent / displayLinkFullName.name.replace(" ", "_")
            shutil.move(str(displayLinkFullName), str(displayLinkNameFix))
            cls.displayLinkFullNameUp = displayLinkNameFix
            displayLinkVer: List[str] = re.findall(r"\d+\.\d+", cls.displayLinkFullNameUp.name)
            displayLinkTarget: str = f"displaylink_{displayLinkVer[0]}"
            cls.displayLinkFileDir = displayLinkFullName.parent / displayLinkTarget
            cls.displayLinkInstallDir = Path(f"/opt/{displayLinkTarget}")


    @classmethod
    def clean_files(cls) -> None:

        if Path(f"{cls.evdiTarPath}/evdi.tar.gz").is_file():
            with suppress(FileNotFoundError):
                os.remove(f"{cls.evdiTarPath}/evdi.tar.gz")
        if cls.evdiGitPath:
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.evdiGitPath)
        if cls.displayLinkFullNameUp and Path(cls.displayLinkFullNameUp).is_file():
            with suppress(FileNotFoundError):
                os.remove(cls.displayLinkFullNameUp)
        if cls.displayLinkInstallDir and cls.displayLinkInstallDir.is_dir():
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.displayLinkInstallDir)
        return


    @classmethod
    def evdi_git_clone(cls) -> None:
        if cls.evdiGitPath.is_dir():
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.evdiGitPath)
            with suppress(FileNotFoundError):
                os.remove(f"{cls.initTmpDir}evdi.tar.gz")

        try:   
            Repo.clone_from(cls.evdiRepo, cls.evdiGitPath)
        except GitCommandError:
            cls.clean_files()


    @classmethod
    def evdi_git_list_util(cls) -> List[TagReference]:
        os.chdir(cls.evdiGitPath)
        cls.localEvdiRepo = git.Repo(cls.evdiGitPath)
        cls.evdiOrigin = cls.localEvdiRepo.remotes.origin

        # Quirky -- may return to subprocess with git commands because it sometimes will list 1.14.5 as the latest version
        # Keep Original with `reverse=True`
        # evdiList: List[TagReference] = sorted(
        #     cls.localEvdiRepo.tags, 
        #     key=lambda t: t.commit.committed_date,
        #     reverse=True
        # )
        cls.evdiList = sorted(
            cls.localEvdiRepo.tags, 
            key=lambda t: t.commit.committed_date
        )

        if not cls.evdiList:
            cls.clean_files()

        return cls.evdiList

    @classmethod
    def find_git_primary(cls) -> str:
        # https://stackoverflow.com/questions/69651536/how-to-get-master-main-branch-from-gitpython
        if not cls.localEvdiRepo:
            cls.localEvdiRepo = git.Repo(cls.evdiGitPath)

        # Run 'git remote show origin'
        evdiRemoteInfo = cls.localEvdiRepo.git.remote("show", "origin")

        # Use regex to find the line: "HEAD branch: main" or "HEAD branch: master"
        match = re.search(r"HEAD branch:\s*(\S+)", evdiRemoteInfo)
        evdiDefaultBranch = match.group(1) if match else "main"
        return evdiDefaultBranch


    @classmethod
    def evdi_pull_tag_util(
        cls,
        evdiDec: str | None = None 
        ) -> None:

        if not evdiDec:
            evdiDec = cls.evdiList[-1] if cls.evdiList else "main"

        if evdiDec != "main":
            evdiGitTag: str = evdiDec
            cls.evdiOrigin.fetch(tags=True)
            evdiBranchTag: str = f"{evdiGitTag}"
            cls.localEvdiRepo.git.checkout("-b", evdiBranchTag, evdiGitTag)

        with tarfile.open(f"{cls.evdiTarPath}/evdi.tar.gz", "w:gz") as tarFile:
            tarFile.add(cls.evdiGitPath, arcname=".")


    @classmethod
    def unzip_displaylink(cls) -> None:

        if cls.displayLinkFullNameUp and cls.displayLinkFileDir:
            with zipfile.ZipFile(cls.displayLinkFullNameUp, 'r') as zipRef:
                zipRef.extractall(cls.displayLinkFileDir)


    @classmethod
    def install_dir_rename(cls) -> None:

        if cls.displayLinkFileDir and cls.displayLinkInstallDir:
            shutil.move(cls.displayLinkFileDir, cls.displayLinkInstallDir)

    @classmethod
    def extract_displaylink_firmware(cls) -> Iterator[str]:

        cls.unzip_displaylink()
        cls.install_dir_rename()

        if not cls.displayLinkInstallDir:
            cls.clean_files()
        else:
            os.chdir(cls.displayLinkInstallDir)
            runFileFind: list[Path] = file_find(cls.displayLinkInstallDir, "*.run")
            runFile: Path | None = runFileFind[0] if runFileFind else None
            if runFile is None:
                cls.clean_files()
            else:
                subprocess.run(["chmod", "+x", runFile])
                extractDisplay = subprocess.Popen(
                    [runFile, "--nox11", "--noprogress", "--noexec", "--keep"],
                    shell=False,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    text=True,
                    bufsize=1
                )
                extractDisplay.wait()

                extractDirFind: list[Path] = dir_find(cls.displayLinkInstallDir, "displaylink-*")
                extractDir: Path | None = extractDirFind[0] if extractDirFind else None
                if extractDir is None:
                    cls.clean_files()
                else:
                    os.chdir(str(extractDir))
                    os.remove("evdi.tar.gz")
                    shutil.move(Path(f"{cls.evdiTarPath}/evdi.tar.gz"), extractDir)
                    subprocess.run(["chmod", "+x", f"{extractDir}/displaylink-installer.sh"])
                    with subprocess.Popen(
                        ["./displaylink-installer.sh", "noreboot"],
                        shell=False, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,
                        text=True, 
                        bufsize=1
                        ) as installProc:
                        assert installProc.stdout is not None
                        for line in installProc.stdout:
                            yield line.rstrip()
                    
                    installProc.wait()
                    if installProc.returncode != 0:
                        yield f"[red]DisplayLink installation failed. Exit code: {installProc.returncode}[/]"

    @staticmethod
    def runit_enable_display() -> None:
        if Path("/var/service/displaylink-driver/down").is_file():
            with suppress(FileNotFoundError):
                os.remove("/var/service/displaylink-driver/down")
        subprocess.run(
            "sv restart displaylink-driver",
            shell=True, 
            capture_output=True, 
            text=True
        )

    @staticmethod
    def systemd_enable_display() -> None:
        displayService: subprocess.CompletedProcess[str] = subprocess.run(
            "systemctl | grep -Ei displaylink",
            shell=True, 
            capture_output=True, 
            text=True
        )
        if displayService.stdout.strip():
            displayServiceUnit: subprocess.CompletedProcess[str] = subprocess.run(
                f"systemctl enable --now {displayServiceUnit.stdout.strip()}",
                shell=True, 
                capture_output=True, 
                text=True
            )



MODAL_MESSAGE = """
[bold]>>> Warning:[/bold] DisplayLink Firmware is already installed. Proceed?

"""


UNINSTALL_MESSAGE = """
[bold]>>> Uninstall the DisplayLink and EVDI Firmware?[/bold]

::: Select [bold]'Yes'[/bold] to uninstall
::: Select [bold]'No'[/bold] to exit the app

[bold]Note:[/bold] 

Uninstalling will require a reboot to fully remove the EVDI software driver and this installer will have to be re-run.
"""

BEGIN_MESSAGE = """
[bold]::: Welcome to the DisplayLink and EVDI installer for linux docking station multi-monitor support.[/bold]


::: Select [bold]'Yes'[/bold] to begin installation
::: Select [bold]'No'[/bold] to exit the app

"""

EVDI_DEC_MESSAGE = """
[bold]::: Please choose the EVDI release version to install:[/bold]

"""

INSTALL_DEC_MESSAGE = """
[bold]::: Install DisplayLink and EVDI?[/bold]


::: Select [bold]'Yes'[/bold] to install
::: Select [bold]'No'[/bold] to delete downloaded files/directories and close the app

"""

EXIT_MESSAGE = """
[bold]::: DisplayLink Installer Complete[/bold]

::: You will need to reboot for the EVDI kernel modules to load
"""

RUNIT_MESSAGE = """
[bold]VOID linux/runit -based distro users:[/bold]
Remember to remove the 'down' service file and restart the 'displaylink-driver' service:

    > cd /var/service/displaylink-driver
    > sudo rm -f down
    > sudo sv restart displaylink-driver
"""

SYSTEMD_MESSAGE = """
[bold]Systemd -based distro users:[/bold]
Remember to check the status of the 'displaylink' service by running:

    > sudo systemctl status displaylink-driver.service
or
    > sudo systemctl status displaylink.service

To start the service if not running: 

    > sudo systemctl enable --now <DISPLAYLINK_SERVICE_NAME>
"""


class ChoiceButton(Button):
    """A button that shifts focus on left/right arrow keys."""

    def on_key(self, event: Key) -> None:
        if event.key == "right":
            self.screen.focus_next()
            event.stop()
        elif event.key == "left":
            self.screen.focus_previous()
            event.stop()


# DisplayLink/EVDI Installed Warning Modal
class InstallModal(ModalScreen[bool]):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="installDialog"):
            yield Static(MODAL_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("No", id="noBtn", classes="dialogQbtn")
                yield ChoiceButton("Yes", id="instBtn", classes="dialogQbtn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "instBtn":
            self.dismiss(True)
        else:
            self.dismiss(False)


# Main DisplayLink/EVDI Uninstall Dialog Screen
class UninstallDialogScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(UNINSTALL_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("Yes", id="yesUnBtn", classes="dialogUnbtn")
                yield ChoiceButton("No", id="noUnBtn", classes="dialogUnbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesUnBtn":
            self.app.push_screen(UninstallIndicatorScreen(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            self.app.exit()


# DisplayLink Uninstall Screen
class UninstallIndicatorScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstalling Synaptics DisplayLink Driver and the EVDI software driver.")
            yield RichLog(id="uninstallLog", highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_uninistallDisplayInd()

    @work(thread=True)
    def exec_uninistallDisplayInd(self) -> None:
        dispLog = self.query_one("#uninstallLog", RichLog)

        for line in self.displayLinkCl.uninstall_display_link():
            self.app.call_from_thread(dispLog.write, line)

        self.app.call_from_thread(self.app.push_screen, UninstallCompleteScreen())


# DisplayLink Uninstallation Complete and Reboot Screen
class UninstallCompleteScreen(Screen):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstall Complete. Restart?")
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("Yes", id="yesReBtn", classes="dialogUnbtn")
                yield ChoiceButton("No", id="noReBtn", classes="dialogUnbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesReBtn":
            subprocess.run(["reboot"], text=True)
        else:
            self.app.exit()


# Main Install Dialog Begin Screen
class BeginInstallScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:
        
        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(BEGIN_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("Yes", id="yesBeginBtn", classes="dialogBeginbtn")
                yield ChoiceButton("No", id="noBeginBtn", classes="dialogBeginbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesBeginBtn":
            self.app.push_screen(DownloadEvdiSoftwareScreen(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            self.app.exit()


# EVDI Software Download Screen
class DownloadEvdiSoftwareScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Cloning the EVDI software driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_pull_evdi()

    @work(thread=True)
    def exec_pull_evdi(self) -> None:
        self.displayLinkCl.evdi_git_clone()
        self.app.call_from_thread(self.app.push_screen, EvdiDecisionScreen(
            displayLinkCl=self.displayLinkCl
        ))


# To-Do: EVDI List Screen
class EvdiDecisionScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        self.evdiGitTagList = displayLinkCl.evdi_git_list_util()
        self.evdiGitPrimary = displayLinkCl.find_git_primary()
        self.evdiGitPull = displayLinkCl.evdi_pull_tag_util
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(EVDI_DEC_MESSAGE)
            yield ListView(
                # Keep for potential list
                # *[ListItem(Label(str(item))) for item in self.evdiGitTagList],
                ListItem(Label(f"{self.evdiGitTagList[-1]} [bold]RECOMMENDED[/bold]"), id=f"{self.evdiGitTagList[-1].name.replace(".", "_")}"),
                ListItem(Label(f"{self.evdiGitPrimary.capitalize()} For Experimental Features. Use at own risk."), id=f"{self.evdiGitPrimary}"),
            )
        yield Footer(id="Footer")

    @on(ListView.Selected)
    def handle_selection(self, event: ListView.Selected) -> None:
        itemId = event.item.id
        self.process_selected_value(itemId)

    def process_selected_value(self, value: str | None) -> None:
        if value:
            self.evdiGitPull(evdiDec=value.replace("_", "."))
            self.app.push_screen(DisplayLinkDownloadScreen(
                displayLinkCl=self.displayLinkCl
            ))


# DisplayLink Software Download Screen
class DisplayLinkDownloadScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Downloading the latest Synaptics DisplayLink Driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_download_display()

    @work(thread=True)
    def exec_download_display(self) -> None:
        self.displayLinkCl.download_displaylink()
        self.app.call_from_thread(self.app.push_screen, BeginDisplayLinkInstallDialogueScreen(
            displayLinkCl=self.displayLinkCl
        ))


# DisplayLink Software Install Screen
class BeginDisplayLinkInstallDialogueScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(INSTALL_DEC_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("Yes", id="yesInstallBtn", classes="dialogInstallbtn")
                yield ChoiceButton("No", id="noInstallBtn", classes="dialogInstallbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesInstallBtn":
            self.app.push_screen(DisplayLinkInstallationScreen(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            # Push to Clean Screen
            self.app.push_screen(CleanFilesExitScreen(
                displayLinkCl=self.displayLinkCl
            ))


# DisplayLink Install Functions Screen
class DisplayLinkInstallationScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Now installing Synaptics DisplayLink Driver.")
            yield Label(">>> Please wait until it finishes...")
            yield RichLog(id="installLog", highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_display_install()

    @work(thread=True)
    def exec_display_install(self) -> None:
        dispLog = self.query_one("#installLog", RichLog)

        for line in self.displayLinkCl.extract_displaylink_firmware():
            self.app.call_from_thread(dispLog.write, line)

        self.app.call_from_thread(self.app.push_screen, CleanFilesExitScreen(
            displayLinkCl=self.displayLinkCl
        ))


# Clean Files and Exit Screen
class CleanFilesExitScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Now removing all downloaded files and exiting.")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_clean_files()

    @work(thread=True)
    def exec_clean_files(self) -> None:
        self.displayLinkCl.clean_files()
        self.app.call_from_thread(self.app.push_screen, FinalizeScreen(displayLinkCl=self.displayLinkCl))


# Finalize Screen 
class FinalizeScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        self.runitTest = self.displayLinkCl.runit_test()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Static(EXIT_MESSAGE)
            if self.runitTest.stdout.strip() == "runit":
                yield Static(RUNIT_MESSAGE, id="finishInstMessage")
            else:
                yield Static(SYSTEMD_MESSAGE, id="finishInstMessage")
            yield Label(">>> Finishing Actions:")
            with Grid(id="horizontalInstBtn"):
                yield ChoiceButton("Yes, Enable Service", id="yesEnBtn", classes="dialogInstallbtn")
                yield ChoiceButton("No, Exit Installer", id="noEnBtn", classes="dialogInstallbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesEnBtn":
            self.app.push_screen(FinishExitScreen(displayLinkCl=self.displayLinkCl))
        else:
            self.app.exit()


# Finish and Exit Screen
class FinishExitScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:

        self.displayLinkCl = displayLinkCl
        self.runitTest = self.displayLinkCl.runit_test()
        self.runitPrepare = self.displayLinkCl.runit_enable_display
        self.systemdPrepare = self.displayLinkCl.systemd_enable_display
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Preparing your system...")
            with Grid(id="horizontalExBtn"):
                yield ChoiceButton("Exit the Installer", id="exitButton", classes="dialogInstallbtn")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.prepare_system()

    @work(thread=True)
    def prepare_system(self) -> None:
        if self.runitTest.stdout.strip() == "runit":
            self.runitPrepare()
        else:
            self.systemdPrepare()
        self.app.call_from_thread(self.prepare_complete)

    def prepare_complete(self) -> None:
        exBtn = self.query_one("#exitButton", Button)
        exBtn.styles.display = "block"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exitButton":
            self.app.exit()


# To-do: Screen to handle Runit displaylink or Systemd

class DisplayLinkInstaller(App):
    BINDINGS = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up", "cursor_up", "Cursor up", show=False),
        Binding("down", "cursor_down", "Cursor down", show=False),
        Binding("left", "move_left", "Move Left", show=False),
        Binding("right", "move_right", "Move Right", show=False),
        Binding(key="q", action="quit", description="Quit the DisplayLink Installer")
    ]

    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        displayLinkCl,
        **kwargs
        ) -> None:
        
        self.displayLinkCl = displayLinkCl
        self.displayLinkInstallCheck = displayLinkCl.displaylink_install_check()
        super().__init__(**kwargs)

    modal_result = reactive[bool | None](None)

    def on_mount(self) -> None:
        self.theme = "nord"

    def on_ready(self) -> None:
        self.push_screen(BeginInstallScreen(
            displayLinkCl=self.displayLinkCl
        ))
        if self.displayLinkInstallCheck:
            self.push_screen(InstallModal(), self.handle_modal_result)

    def handle_modal_result(self, result: bool | None) -> None:
        self.modal_result = result

    def watch_modal_result(self, old_value: bool | None, new_value: bool | None) -> None:
        if new_value is not None:
            if not new_value:
                self.exit()
            else:
                self.push_screen(UninstallDialogScreen(
                    displayLinkCl=self.displayLinkCl
                ))


if __name__ == "__main__":
    app = DisplayLinkInstaller(displayLinkCl=DispLink)
    app.run()
