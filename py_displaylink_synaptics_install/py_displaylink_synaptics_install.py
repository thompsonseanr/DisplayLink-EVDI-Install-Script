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
from textual.events import Print
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Header, Footer, RichLog, Welcome, Label, Button
from textual.widgets import Placeholder, Static, LoadingIndicator

# Personal Dev Notes: 
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
    localEvdiRepo: git.repo.base.Repo
    displayLinkFullNameUp: Path
    displayLinkFileDir: Path
    displayLinkInstallDir: Path

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

    # Fix return type and refactor. Convert to subprocess.Popen
    @classmethod
    def uninstall_display_link(cls) -> bool:
        dlTest = cls.displaylink_install_check()
        if dlTest:
            # print("uninstalling")
            dlUnSub: subprocess.CompletedProcess[str] = subprocess.run("displaylink-installer uninstall", 
                shell=True,
                capture_output=True,
                text=True
            )
            return dlUnSub
        #     return False if dlUnSub.returncode != 0 else True
        # else:
        #     return False

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
    def evdi_git_list_util(cls) -> List[TagReference]:

        if cls.evdiGitPath.is_dir():
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.evdiGitPath)
            with suppress(FileNotFoundError):
                os.remove(f"{cls.initTmpDir}evdi.tar.gz")

        try:   
            Repo.clone_from(cls.evdiRepo, cls.evdiGitPath)
        except GitCommandError:
            cls.clean_files()

        os.chdir(cls.evdiGitPath)
        cls.localEvdiRepo = git.Repo(cls.evdiGitPath)
        cls.evdiOrigin = cls.localEvdiRepo.remotes.origin

        evdiList: List[TagReference] = sorted(
            cls.localEvdiRepo.tags, 
            key=lambda t: t.commit.committed_date, 
            reverse=True
        )

        if not evdiList:
            cls.clean_files()

        return evdiList


    @classmethod
    def evdi_pull_tag_util(
        cls,
        evList: List[TagReference],
        evdiDec: int = 0
        ) -> None:

        evdiGitTag: str = evList[evdiDec].name
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

    # Fix return type and refactor 
    @classmethod
    def extract_displaylink_firmware(cls) -> None:

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
                try:
                    # Triggers a shell window that I need to fix. Convert ot subprocess.Popen and change try/except
                    subprocess.run([runFile, "--noexec", "--keep"], 
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    if e.returncode == 1:
                        os.chdir("/opt")
                        cls.clean_files()

                extractDirFind: list[Path] = dir_find(cls.displayLinkInstallDir, "displaylink-*")
                extractDir: Path | None = extractDirFind[0] if extractDirFind else None
                if extractDir is None:
                    cls.clean_files()
                else:
                    os.chdir(str(extractDir))
                    os.remove("evdi.tar.gz")
                    shutil.move(Path(f"{cls.evdiTarPath}/evdi.tar.gz"), extractDir)
                    subprocess.run(["chmod", "+x", f"{extractDir}/displaylink-installer.sh"])
                    # Refactor to subprocess.Popen
                    return subprocess.run(["./displaylink-installer.sh", "noreboot"],
                        capture_output=True,
                        text=True
                    )


MODAL_MESSAGE = """
[bold]>>> Warning:[/bold] DisplayLink Firmware is already installed. Proceed?

::: Navigate using `Tab`
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

::: Navigate using `Tab`

::: Select [bold]'Yes'[/bold] to begin installation
::: Select [bold]'No'[/bold] to exit the app

"""

EVDI_DEC_MESSAGE = """
[bold]::: Would you like to choose a particular EVDI release version to install or go with the latest?[/bold]

::: Navigate using `Tab`

::: Select [bold]'Yes'[/bold] to install with the latest release tag
::: Select [bold]'No'[/bold] to choose a version of EVDI from a list

"""

INSTALL_DEC_MESSAGE = """
[bold]::: Install DisplayLink and EVDI?[/bold]

::: Navigate using `Tab`

::: Select [bold]'Yes'[/bold] to install
::: Select [bold]'No'[/bold] to delete downloaded files/directories and close the app

"""


# DisplayLink/EVDI Installed Warning Modal
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
                yield Button("Yes", id="yesUnBtn", classes="dialogUnbtn")
                yield Button("No", id="noUnBtn", classes="dialogUnbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesUnBtn":
            self.app.push_screen(UninstallIndicatorScreen(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            self.app.exit()


# DisplayLink Uninstall Animation Screen
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
            yield LoadingIndicator()
            # yield RichLog(highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_uninistallDisplayInd()

    @work(thread=True)
    def exec_uninistallDisplayInd(self) -> None:
        # dispLog = self.query_one(RichLog)
        dispRes = self.displayLinkCl.uninstall_display_link()

        # if dispRes.stdout:
        #     dispLog.write(dispRes.stdout)
        # if dispRes.stderr:
        #     dispLog.write(f"[red]STDERR:[/] {dispRes.stderr}")

        self.app.call_from_thread(self.app.push_screen, UninstallCompleteScreen())


# DisplayLink Uninstallation Complete and Reboot Screen
class UninstallCompleteScreen(Screen):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstall Complete. Restart?")
            with Grid(id="horizontalInstBtn"):
                yield Button("Yes", id="yesReBtn", classes="dialogUnbtn")
                yield Button("No", id="noReBtn", classes="dialogUnbtn")
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
                yield Button("Yes", id="yesBeginBtn", classes="dialogBeginbtn")
                yield Button("No", id="noBeginBtn", classes="dialogBeginbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesBeginBtn":
            self.app.push_screen(EvdiDecisionScreen(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            self.app.exit()


# EVDI Decision Screen
class EvdiDecisionScreen(Screen):
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
            yield Static(EVDI_DEC_MESSAGE)
            with Grid(id="horizontalInstBtn"):
                yield Button("Yes", id="yesBeginBtn", classes="dialogBeginbtn")
                yield Button("No", id="noBeginBtn", classes="dialogBeginbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesBeginBtn":
            # Push List Screen. To-Do: EVDI List Screen
            self.app.push_screen(DownloadEvdiSoftware(
                displayLinkCl=self.displayLinkCl
            ))
        else:
            # Push to Download Indicator
            self.app.push_screen(DownloadEvdiSoftware(
                displayLinkCl=self.displayLinkCl
            ))

# To-Do: EVDI List Screen

# EVDI Software Download Screen
class DownloadEvdiSoftware(Screen):
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
        localEvdiList = self.displayLinkCl.evdi_git_list_util()
        self.displayLinkCl.evdi_pull_tag_util(localEvdiList)
        self.app.call_from_thread(self.app.push_screen, DisplayLinkDownloadScreen(
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
                yield Button("Yes", id="yesInstallBtn", classes="dialogInstallbtn")
                yield Button("No", id="noInstallBtn", classes="dialogInstallbtn")
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
            yield LoadingIndicator()
            # yield RichLog(highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_display_install()

    @work(thread=True)
    def exec_display_install(self) -> None:
        # dispLog = self.query_one(RichLog)
        dispRes = self.displayLinkCl.extract_displaylink_firmware()

        # if dispRes.stdout:
        #     dispLog.write(dispRes.stdout)
        # if dispRes.stderr:
        #     dispLog.write(f"[red]STDERR:[/] {dispRes.stderr}")

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
        self.app.call_from_thread(self.app.push_screen, ExitScreen())


# Exit Screen - Needs work - Maybe a close button?
class ExitScreen(Screen):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            # Create dynamic exit messages like the bash script
            # yield Static(EXIT_MESSAGES)
            yield Label(">>> Exit the installer?")
            with Grid(id="horizontalInstBtn"):
                yield Button("Yes", id="yesQuitBtn", classes="dialogInstallbtn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesQuitBtn":
            self.app.exit()


class DisplayLinkInstaller(App):
    BINDINGS = [
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
