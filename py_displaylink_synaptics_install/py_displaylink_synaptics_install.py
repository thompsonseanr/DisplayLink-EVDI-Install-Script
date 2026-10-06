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
runitTest: subprocess.CompletedProcess[str] = subprocess.run(
    "ps -p 1 -o comm=",
    shell=True, 
    capture_output=True, 
    text=True
)


initTmpDir: Path = Path("/tmp/")
evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
evdiGitPath: Path = Path("/tmp/evdi")
evdiTarPath: str = os.path.dirname(evdiGitPath)
evdiOrigin: git.remote.Remote
localEvdiRepo: git.repo.base.Repo

installDec: bool | None = None
testDec: bool | None = None


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


def uninstall_display_link() -> bool:
    dlTest = displaylink_install_check()
    if dlTest:
        print("uninstalling")
        dlUnSub: subprocess.CompletedProcess[str] = subprocess.run(
            "displaylink-installer uninstall", 
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
displayLinkFullNameUp: Path
displayLinkFileDir: Path
displayLinkInstallDir: Path

def download_displaylink() -> None:
    global displayLinkFullNameUp
    global displayLinkFileDir
    global displayLinkInstallDir

    displayLinkFullNameFindArt: list[Path] = file_find(initTmpDir, "DisplayLink*.zip")
    if displayLinkFullNameFindArt:
        for fd in displayLinkFullNameFindArt:
            if fd and fd.is_file():
                os.remove(fd)

    py_playwright_scraper.py_scraper()

    displayLinkFullNameFind: list[Path] = file_find(initTmpDir, "DisplayLink*.zip")
    displayLinkFullName: Path | None = displayLinkFullNameFind[0] if displayLinkFullNameFind else None
    if not displayLinkFullName:
        sys.exit(1)
    else:
        displayLinkPath: Path = displayLinkFullName.parent
        displayLinkName: str = displayLinkFullName.name
        displayLinkNameFix: Path = displayLinkFullName.parent / displayLinkFullName.name.replace(" ", "_")
        # displayLinkFullNameUp = displayLinkFullName.rename(displayLinkNameFix)
        shutil.move(str(displayLinkFullName), str(displayLinkNameFix))
        displayLinkFullNameUp = displayLinkNameFix
        displayLinkVer: List[str] = re.findall(r"\d+\.\d+", displayLinkFullNameUp.name)
        version_str = displayLinkVer[0] if displayLinkVer else "6.3"
        displayLinkTarget: str = f"displaylink_{displayLinkVer[0]}"
        displayLinkFileDir = displayLinkFullName.parent / displayLinkTarget
        displayLinkInstallDir = Path(f"/opt/{displayLinkTarget}")


def clean_files(
    evdiTp: str = evdiTarPath,
    evdiGp: Path = evdiGitPath,
    dlfnUp: Optional[Path] = None,
    dliDir: Optional[Path] = None
    # sysEx: int = 0
    ) -> None:

    if dlfnUp is None:
        dlfnUp = displayLinkFullNameUp
    if dliDir is None:
        dliDir = displayLinkInstallDir

    if Path(f"{evdiTp}/evdi.tar.gz").is_file():
        with suppress(FileNotFoundError):
            os.remove(f"{evdiTp}/evdi.tar.gz")
    if evdiGp:
        with suppress(FileNotFoundError):
            shutil.rmtree(evdiGp)
    if dlfnUp and Path(dlfnUp).is_file():
        with suppress(FileNotFoundError):
            os.remove(dlfnUp)
    if dliDir and dliDir.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree(dliDir)
    # return sys.exit(sysEx)
    return


def evdi_git_list_util(
    evdiGp: Path = evdiGitPath,
    evdiTp: str = evdiTarPath,
    evdiGr: str = evdiRepo,
    initTd: Path = initTmpDir
    ) -> List[TagReference]:

    global evdiOrigin
    global localEvdiRepo
    evdiGitMain: str

    if evdiGp.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree(evdiGp)
        with suppress(FileNotFoundError):
            os.remove(f"{initTd}evdi.tar.gz")

    try:   
        Repo.clone_from(evdiGr, evdiGp)
    except GitCommandError:
        clean_files()

    os.chdir(evdiGp)
    localEvdiRepo = git.Repo(evdiGp)
    evdiOrigin = localEvdiRepo.remotes.origin

    evdiList: List[TagReference] = sorted(
        localEvdiRepo.tags, 
        key=lambda t: t.commit.committed_date, 
        reverse=True
    )

    if not evdiList:
        clean_files()

    return evdiList


def evdi_pull_tag_util(
    evList: List[TagReference],
    evdiGp: Path = evdiGitPath,
    evdiDec: int = 0,
    evdiTp: str = evdiTarPath,
    ) -> None:

    global localEvdiRepo
    evdiGitTag: str = evList[evdiDec].name
    evdiOrigin.fetch(tags=True)
    evdiBranchTag: str = f"{evdiGitTag}"
    localEvdiRepo.git.checkout("-b", evdiBranchTag, evdiGitTag)

    with tarfile.open(f"{evdiTp}/evdi.tar.gz", "w:gz") as tarFile:
        tarFile.add(evdiGp, arcname=".")


def unzip_displaylink(
    # dlfnUp: Optional[Path] = None,
    # dlfDir: Optional[Path] = None
    ) -> None:

    # if dlfnUp is None:
    #     dlfnUp = displayLinkFullNameUp
    if dlfDir is None:
        dlfDir = displayLinkFileDir

    # Must create local variables -- passed variables are breaking
    dlfnUpFind: list[Path] = file_find(initTmpDir, "DisplayLink*.zip")
    dlfnUp: Path | None = dlfnUpFind[0] if dlfnUpFind else None
        # displayLinkPath: Path = displayLinkFullName.parent
        # displayLinkName: str = displayLinkFullName.name
        # displayLinkNameFix: Path = displayLinkFullName.parent / displayLinkFullName.name.replace(" ", "_")
        # # displayLinkFullNameUp = displayLinkFullName.rename(displayLinkNameFix)
        # shutil.move(str(displayLinkFullName), str(displayLinkNameFix))
        # displayLinkFullNameUp = displayLinkNameFix
        # # displayLinkVer: List[str] = re.findall(r"\d+\.\d+", displayLinkFullNameUp.name)
        # displayLinkVer: List[str] = re.findall(r"\d+\.\d+", displayLinkFullNameUp.name)
        # version_str = displayLinkVer[0] if displayLinkVer else "6.3"

        # displayLinkTarget: str = f"displaylink_{displayLinkVer[0]}"
        # displayLinkFileDir = displayLinkFullName.parent / displayLinkTarget
        # displayLinkInstallDir = Path(f"/opt/{displayLinkTarget}")

    if dlfnUp and dlfDir:
        with zipfile.ZipFile(dlfnUp, 'r') as zipRef:
            zipRef.extractall(dlfDir)

    # FIX 3: Add explicit file checks and directory auto-creation
    # if dlfnUp and dlfnUp.is_file() and dlfDir:
    #     dlfDir.mkdir(parents=True, exist_ok=True)
    #     with zipfile.ZipFile(dlfnUp, 'r') as zipRef:
    #         zipRef.extractall(dlfDir)
    # else:
    #     raise FileNotFoundError(f"Cannot unzip; target archive missing or invalid: {dlfnUp}")

def install_dir_rename(
    dlfDir: Optional[Path] = None,
    dliDir: Optional[Path] = None
    ) -> None:

    if dlfDir is None:
        dlfDir = displayLinkFileDir
    if dliDir is None:
        dliDir = displayLinkInstallDir
    
    if dlfDir and dliDir:
        shutil.move(dlfDir, dliDir)



def extract_displaylink_firmware(
    dliDir: Optional[Path] = None,
    evdiTp: str = evdiTarPath
    ) -> None:
    
    if dliDir is None:
        dliDir = displayLinkInstallDir

    if not dliDir:
        clean_files()
    else:
        os.chdir(dliDir)
        runFileFind: list[Path] = file_find(dliDir, "*.run")
        runFile: Path | None = runFileFind[0] if runFileFind else None
        if runFile is None:
            clean_files()
        else:
            subprocess.run(["chmod", "+x", runFile], check=True)
            try:
                subprocess.run([runFile, "--noexec", "--keep"], check=True)
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    os.chdir("/opt")
                    clean_files()

            extractDirFind: list[Path] = dir_find(dliDir, "displaylink-*")
            extractDir: Path | None = extractDirFind[0] if extractDirFind else None
            if extractDir is None:
                clean_files()
            else:
                os.chdir(str(extractDir))
                os.remove("evdi.tar.gz")
                shutil.move(Path(f"{evdiTp}/evdi.tar.gz"), extractDir)
                subprocess.run(["chmod", "+x", f"{extractDir}/displaylink-installer.sh"], check=True)
                subprocess.run(["./displaylink-installer.sh", "noreboot"], check=True)


    # Menu to capture evdi decision, then do the remaining operations
    #
    # download_displaylink()
    # evdi_git_list_util()
    # evdi_pull_tag_util()
    # unzip_displaylink()
    # install_dir_rename()
    # extract_displaylink_firmware()
    # clean_files()


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
        uninstallDisplay,
        **kwargs
        ) -> None:

        self.uninstallDisplay = uninstallDisplay
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
            self.app.push_screen(UninstallIndicatorScreen(uninstallDisplay=self.uninstallDisplay))
        else:
            self.app.exit()


# DisplayLink Uninstall Animation Screen
class UninstallIndicatorScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        uninstallDisplay, 
        **kwargs
        ) -> None:

        self.uninstallDisplay = uninstallDisplay
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Uninstalling Synaptics DisplayLink Driver and the EVDI software driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_uninistallDisplayInd()

    @work(thread=True)
    def exec_uninistallDisplayInd(self) -> None:
        self.uninstallDisplay()
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
        evdiGitList,
        evdiPullTag,
        downloadDisplayLink,
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.evdiGitList = evdiGitList
        self.evdiPullTag = evdiPullTag
        self.downloadDisplayLink = downloadDisplayLink
        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
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
                evdiGitList=self.evdiGitList, 
                evdiPullTag=self.evdiPullTag, 
                downloadDisplayLink=self.downloadDisplayLink,
                unzipDisplaylink=self.downloadDisplayLink,
                installDirRename=self.installDirRename,
                extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
                cleanFiles=self.cleanFiles
            ))
        else:
            self.app.exit()


# EVDI Decision Screen
class EvdiDecisionScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        evdiGitList,
        evdiPullTag,
        downloadDisplayLink,
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.evdiGitList = evdiGitList
        self.evdiPullTag = evdiPullTag
        self.downloadDisplayLink = downloadDisplayLink
        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
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
            # Push List Screen
            self.app.push_screen(DownloadEvdiSoftware(
                evdiGitList=self.evdiGitList, 
                evdiPullTag=self.evdiPullTag, 
                downloadDisplayLink=self.downloadDisplayLink,
                unzipDisplaylink=self.downloadDisplayLink,
                installDirRename=self.installDirRename,
                extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
                cleanFiles=self.cleanFiles
            ))
        else:
            # Push to Download Indicator
            self.app.push_screen(DownloadEvdiSoftware(
                evdiGitList=self.evdiGitList, 
                evdiPullTag=self.evdiPullTag, 
                downloadDisplayLink=self.downloadDisplayLink,
                unzipDisplaylink=self.downloadDisplayLink,
                installDirRename=self.installDirRename,
                extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
                cleanFiles=self.cleanFiles
            ))

# EVDI Software Download Screen
class DownloadEvdiSoftware(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        evdiGitList, 
        evdiPullTag,
        downloadDisplayLink,
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.evdiGitList = evdiGitList
        self.evdiPullTag = evdiPullTag
        self.downloadDisplayLink = downloadDisplayLink
        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
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
        localEvdiList = self.evdiGitList()
        self.evdiPullTag(localEvdiList)
        self.app.call_from_thread(self.app.push_screen, DisplayLinkDownloadScreen(
                downloadDisplayLink=self.downloadDisplayLink,
                unzipDisplaylink=self.downloadDisplayLink,
                installDirRename=self.installDirRename,
                extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
                cleanFiles=self.cleanFiles
        ))


# DisplayLink Software Download Screen
class DisplayLinkDownloadScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        downloadDisplayLink,
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.downloadDisplayLink = downloadDisplayLink
        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
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
        self.downloadDisplayLink()
        self.app.call_from_thread(self.app.push_screen, BeginDisplayLinkInstallDialogueScreen(
            unzipDisplaylink=self.downloadDisplayLink,
            installDirRename=self.installDirRename,
            extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
            cleanFiles=self.cleanFiles
        ))

# Function execution order:
# unzip_displaylink()
# install_dir_rename()
# extract_displaylink_firmware()
# clean_files

# DisplayLink Software Install Screen
class BeginDisplayLinkInstallDialogueScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
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
            # Push DisplayLinkInstallationScreen Screen
            self.app.push_screen(DisplayLinkInstallationScreen(
                unzipDisplaylink=self.unzipDisplaylink,
                installDirRename=self.installDirRename,
                extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
                cleanFiles=self.cleanFiles
            ))
        else:
            # Push to Clean Screen
            self.app.push_screen(CleanFilesExitScreen(
                cleanFiles=self.cleanFiles
            ))


# DisplayLink Install Functions Screen
class DisplayLinkInstallationScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:

        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Now installing Synaptics DisplayLink Driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_display_install()

    @work(thread=True)
    def exec_display_install(self) -> None:
        self.unzipDisplaylink()
        self.installDirRename()
        self.extractDisplaylinkFirmware()
        self.app.call_from_thread(self.app.push_screen, CleanFilesExitScreen(cleanFiles=self.cleanFiles))


# Clean Files and Exit Screen
class CleanFilesExitScreen(Screen):
    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        cleanFiles,
        **kwargs
        ) -> None:

        self.cleanFiles = cleanFiles
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
        self.cleanFiles()
        self.app.call_from_thread(self.app.push_screen, ExitScreen())


class ExitScreen(Screen):
    CSS_PATH = "styles.tcss"

    def on_mount(self) -> None:
        time.sleep(5) 
        self.app.exit()

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="unDispDialog"):
            yield Label(">>> Now Exiting")
        yield Footer(id="Footer")


# DisplayLink Installation Complete Screen


# Main Install Dialog Container and Screen -- Keep for reference
# class IntroContainer(Container):
#     CSS_PATH = "styles.tcss"

#     # Container for DisplayLink/Evdi Events
#     def compose(self) -> ComposeResult:
#         yield Label(f"::: Hello.", id="installDec")


# class AppScreen(Screen):
#     CSS_PATH = "styles.tcss"

#     def compose(self) -> ComposeResult:
#         yield Header(id="Header")
#         yield IntroContainer()
#         yield Footer(id="Footer")

# Function execution order:
# unzip_displaylink()
# install_dir_rename()
# extract_displaylink_firmware()
# clean_files()

class DisplayLinkInstaller(App):
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the DisplayLink Installer")
    ]

    CSS_PATH = "styles.tcss"

    def __init__(
        self, 
        displayLinkInstallCheck, 
        uninstallDisplay, 
        evdiGitList,
        evdiPullTag,
        downloadDisplayLink,
        unzipDisplaylink,
        installDirRename,
        extractDisplaylinkFirmware,
        cleanFiles,
        **kwargs
        ) -> None:
        self.displayLinkInstallCheck = displayLinkInstallCheck()
        # self.displayLinkInstallCheck = False
        self.uninstallDisplay = uninstallDisplay
        self.evdiGitList = evdiGitList
        self.evdiPullTag = evdiPullTag
        self.downloadDisplayLink = downloadDisplayLink
        self.unzipDisplaylink = unzipDisplaylink
        self.installDirRename = installDirRename
        self.extractDisplaylinkFirmware = extractDisplaylinkFirmware
        self.cleanFiles = cleanFiles
        super().__init__(**kwargs)

    modal_result = reactive[bool | None](None)

    def on_mount(self) -> None:
        self.theme = "nord"

    def on_ready(self) -> None:
        self.push_screen(BeginInstallScreen(
            evdiGitList=self.evdiGitList, 
            evdiPullTag=self.evdiPullTag, 
            downloadDisplayLink=self.downloadDisplayLink,
            unzipDisplaylink=self.downloadDisplayLink,
            installDirRename=self.installDirRename,
            extractDisplaylinkFirmware=self.extractDisplaylinkFirmware,
            cleanFiles=self.cleanFiles
        ))
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
                self.push_screen(UninstallDialogScreen(uninstallDisplay=self.uninstallDisplay))


if __name__ == "__main__":
    app = DisplayLinkInstaller(
        displayLinkInstallCheck=displaylink_install_check,
        uninstallDisplay=uninstall_display_link,
        evdiGitList=evdi_git_list_util,
        evdiPullTag=evdi_pull_tag_util,
        downloadDisplayLink=download_displaylink,
        unzipDisplaylink=unzip_displaylink,
        installDirRename=install_dir_rename,
        extractDisplaylinkFirmware=extract_displaylink_firmware,
        cleanFiles=clean_files
        )
    app.run()
