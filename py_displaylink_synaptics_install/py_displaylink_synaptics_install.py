import os
import socket
import shutil
import sys
import subprocess
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
# DisplayLink installer was created with `makeself`
# Playwright drivers will have to be installed with this ENV for pyinstaller:
# PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium
# Build with:
# pyinstaller --onefile --add-data "styles.tcss:." py_displaylink_synaptics_install.py

if os.getuid() != 0:
    print("Please run this script with `sudo`. Exiting.")
    sys.exit(1)


def dir_find(init_search_dir: Path, target_obj: str) -> list[Path]:
    return [d for d in Path(init_search_dir).rglob(target_obj) if d.is_dir()]

def file_find(init_search_dir: Path, target_obj: str) -> list[Path]:
    return [f for f in Path(init_search_dir).rglob(target_obj) if f.is_file()]


class DispLink:

    init_tmp_dir: Path = Path("/tmp/")
    evdi_repo: str = "https://github.com/DisplayLink/evdi.git"
    evdi_git_path: Path = Path("/tmp/evdi")
    evdi_tar_path: str = os.path.dirname(evdi_git_path)
    evdi_origin: git.remote.Remote
    evdi_list: List[TagReference]
    local_evdi_repo: git.repo.base.Repo
    displaylink_full_name_up: Path | None = None
    displaylink_file_dir: Path | None = None
    displaylink_install_dir: Path | None = None


    # https://stackoverflow.com/questions/20913411/test-if-an-internet-connection-is-present-in-python
    @staticmethod
    def connection_check(host="1.1.1.1", port=443, timeOut=3) -> bool:
        try:
            socket.setdefaulttimeout(timeOut)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
            return True
        except(socket.error, OSError):
            pass

        return False


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
        evdi_test: subprocess.CompletedProcess[str] = subprocess.run(
            f'lsmod | grep -Eio "evdi" | head -1', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        display_installer_test: Path = Path("/usr/bin/displaylink-installer")
        is_displaylink_installed: bool = True if (evdi_test.stdout and display_installer_test.is_file()) else False
        return is_displaylink_installed

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
        displaylink_fullname_find_art: list[Path] = file_find(cls.init_tmp_dir, "DisplayLink*.zip")
        if displaylink_fullname_find_art:
            for fd in displaylink_fullname_find_art:
                if fd and fd.is_file():
                    os.remove(fd)

        py_playwright_scraper.py_scraper()

        displaylink_fullname_find: list[Path] = file_find(cls.init_tmp_dir, "DisplayLink*.zip")
        displaylink_fullname: Path | None = displaylink_fullname_find[0] if displaylink_fullname_find else None
        if not displaylink_fullname:
            sys.exit(1)
        else:
            displaylink_path: Path = displaylink_fullname.parent
            displaylink_name: str = displaylink_fullname.name
            displaylink_name_fix: Path = displaylink_fullname.parent / displaylink_fullname.name.replace(" ", "_")
            shutil.move(str(displaylink_fullname), str(displaylink_name_fix))
            cls.displaylink_full_name_up = displaylink_name_fix
            displaylink_ver: List[str] = re.findall(r"\d+\.\d+", cls.displaylink_full_name_up.name)
            displayLinkTarget: str = f"displaylink_{displaylink_ver[0]}"
            cls.displaylink_file_dir = displaylink_fullname.parent / displayLinkTarget
            cls.displaylink_install_dir = Path(f"/opt/{displayLinkTarget}")


    @classmethod
    def clean_files(cls) -> None:

        if Path(f"{cls.evdi_tar_path}/evdi.tar.gz").is_file():
            with suppress(FileNotFoundError):
                os.remove(f"{cls.evdi_tar_path}/evdi.tar.gz")
        if cls.evdi_git_path:
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.evdi_git_path)
        if cls.displaylink_full_name_up and Path(cls.displaylink_full_name_up).is_file():
            with suppress(FileNotFoundError):
                os.remove(cls.displaylink_full_name_up)
        if cls.displaylink_install_dir and cls.displaylink_install_dir.is_dir():
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.displaylink_install_dir)
        return


    @classmethod
    def evdi_git_clone(cls) -> None:
        if cls.evdi_git_path.is_dir():
            with suppress(FileNotFoundError):
                shutil.rmtree(cls.evdi_git_path)
            with suppress(FileNotFoundError):
                os.remove(f"{cls.init_tmp_dir}evdi.tar.gz")

        try:   
            Repo.clone_from(cls.evdi_repo, cls.evdi_git_path)
        except GitCommandError:
            cls.clean_files()


    @classmethod
    def evdi_git_list_util(cls) -> List[TagReference]:
        os.chdir(cls.evdi_git_path)
        cls.local_evdi_repo = git.Repo(cls.evdi_git_path)
        cls.evdi_origin = cls.local_evdi_repo.remotes.origin

        cls.evdi_list = sorted(
            cls.local_evdi_repo.tags, 
            key=lambda t: t.commit.committed_date
        )

        if not cls.evdi_list:
            cls.clean_files()

        return cls.evdi_list

    @classmethod
    def find_git_primary(cls) -> str:
        # https://stackoverflow.com/questions/69651536/how-to-get-master-main-branch-from-gitpython
        if not cls.local_evdi_repo:
            cls.local_evdi_repo = git.Repo(cls.evdi_git_path)

        # Run 'git remote show origin'
        evdi_remote_info = cls.local_evdi_repo.git.remote("show", "origin")

        # Use regex to find the line: "HEAD branch: main" or "HEAD branch: master"
        match = re.search(r"HEAD branch:\s*(\S+)", evdi_remote_info)
        evdi_default_branch = match.group(1) if match else "main"
        return evdi_default_branch


    @classmethod
    def evdi_pull_tag_util(
        cls,
        evdi_dec: str | None = None 
        ) -> None:

        if not evdi_dec:
            evdi_dec = cls.evdi_list[-1] if cls.evdi_list else "main"

        if evdi_dec != "main":
            evdi_git_tag: str = evdi_dec
            cls.evdi_origin.fetch(tags=True)
            evdiBranchTag: str = f"{evdi_git_tag}"
            cls.local_evdi_repo.git.checkout("-b", evdiBranchTag, evdi_git_tag)

        with tarfile.open(f"{cls.evdi_tar_path}/evdi.tar.gz", "w:gz") as tar_file:
            tar_file.add(cls.evdi_git_path, arcname=".")


    @classmethod
    def unzip_displaylink(cls) -> None:

        if cls.displaylink_full_name_up and cls.displaylink_file_dir:
            with zipfile.ZipFile(cls.displaylink_full_name_up, 'r') as zip_ref:
                zip_ref.extractall(cls.displaylink_file_dir)


    @classmethod
    def install_dir_rename(cls) -> None:

        if cls.displaylink_file_dir and cls.displaylink_install_dir:
            shutil.move(cls.displaylink_file_dir, cls.displaylink_install_dir)

    @classmethod
    def extract_displaylink_firmware(cls) -> Iterator[str]:

        cls.unzip_displaylink()
        cls.install_dir_rename()

        if not cls.displaylink_install_dir:
            cls.clean_files()
        else:
            os.chdir(cls.displaylink_install_dir)
            run_file_find: list[Path] = file_find(cls.displaylink_install_dir, "*.run")
            run_file: Path | None = run_file_find[0] if run_file_find else None
            if run_file is None:
                cls.clean_files()
            else:
                subprocess.run(["chmod", "+x", run_file])
                # `makeself` commands -- https://makeself.io/
                extract_display = subprocess.Popen(
                    [run_file, "--nox11", "--noprogress", "--noexec", "--keep"],
                    shell=False,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    text=True,
                    bufsize=1
                )
                extract_display.wait()

                extract_dir_find: list[Path] = dir_find(cls.displaylink_install_dir, "displaylink-*")
                extract_dir: Path | None = extract_dir_find[0] if extract_dir_find else None
                if extract_dir is None:
                    cls.clean_files()
                else:
                    os.chdir(str(extract_dir))
                    os.remove("evdi.tar.gz")
                    shutil.move(Path(f"{cls.evdi_tar_path}/evdi.tar.gz"), extract_dir)
                    subprocess.run(["chmod", "+x", f"{extract_dir}/displaylink-installer.sh"])
                    with subprocess.Popen(
                        ["./displaylink-installer.sh", "noreboot"],
                        shell=False, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,
                        text=True, 
                        bufsize=1
                        ) as install_proc:
                        assert install_proc.stdout is not None
                        for line in install_proc.stdout:
                            yield line.rstrip()
                    
                    install_proc.wait()
                    if install_proc.returncode != 0:
                        yield f"[red]DisplayLink installation failed. Exit code: {install_proc.returncode}[/]"

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
        display_service: subprocess.CompletedProcess[str] = subprocess.run(
            "systemctl | grep -Ei displaylink",
            shell=True, 
            capture_output=True, 
            text=True
        )

        display_service_name = display_service.stdout.strip()
        
        if display_service_name:
            display_service_unit: subprocess.CompletedProcess[str] = subprocess.run(
                f"systemctl restart {display_service_name}",
                shell=True, 
                capture_output=True, 
                text=True
            )


CONNECTION_MESSAGE = """
[bold]>>> Warning:[/bold] Please connect to the internet before proceeding with the DisplayLink installer.
"""

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

UNINSTALLATION_LOG_MESSAGE = """
>>> Uninstalling Synaptics DisplayLink Driver and the EVDI software driver.

>>> Please be patient as it completes...

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

INSTALLATION_LOG_MESSAGE = """
>>> Now installing Synaptics DisplayLink Driver.
>>> Please wait until it finishes... (Building the EVDI DKMS kernel module takes time)

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


# Buttons with right/left arrow key focus
class ChoiceButton(Button):
    
    def on_key(self, event: Key) -> None:
        if event.key == "right":
            self.screen.focus_next()
            event.stop()
        elif event.key == "left":
            self.screen.focus_previous()
            event.stop()


# DisplayLink/EVDI Installed Warning Modal
class NoConnectionModal(ModalScreen[bool]):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="install-dialog"):
            yield Static(CONNECTION_MESSAGE)
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Exit Installer", id="no-btn", classes="dialog-q-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(False)


# DisplayLink/EVDI Installed Warning Modal
class InstallModal(ModalScreen[bool]):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="install-dialog"):
            yield Static(MODAL_MESSAGE)
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("No", id="no-btn", classes="dialog-q-btn")
                yield ChoiceButton("Yes", id="inst-btn", classes="dialog-q-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "inst-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)


# Main DisplayLink/EVDI Uninstall Dialog Screen
class UninstallDialogScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self, 
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(UNINSTALL_MESSAGE)
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Yes", id="yesUnBtn", classes="dialog-un-btn")
                yield ChoiceButton("No", id="noUnBtn", classes="dialog-un-btn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yesUnBtn":
            self.app.push_screen(UninstallIndicatorScreen(
                displaylink_cl=self.displaylink_cl
            ))
        else:
            self.app.exit()


# DisplayLink Uninstall Screen
class UninstallIndicatorScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(UNINSTALLATION_LOG_MESSAGE)
            yield RichLog(id="uninstall-log", highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_uninistallDisplayInd()

    @work(thread=True)
    def exec_uninistallDisplayInd(self) -> None:
        dispLog = self.query_one("#uninstall-log", RichLog)

        for line in self.displaylink_cl.uninstall_display_link():
            self.app.call_from_thread(dispLog.write, line)

        self.app.call_from_thread(self.app.push_screen, UninstallCompleteScreen())


# DisplayLink Uninstallation Complete and Reboot Screen
class UninstallCompleteScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Label(">>> Uninstall Complete. Restart?")
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Yes", id="yes-re-btn", classes="dialog-un-btn")
                yield ChoiceButton("No", id="no-re-btn", classes="dialog-un-btn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-re-btn":
            subprocess.run(["reboot"], text=True)
        else:
            self.app.exit()


# Main Install Dialog Begin Screen
class BeginInstallScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:
        
        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(BEGIN_MESSAGE)
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Yes", id="yes-begin-btn", classes="dialog-begin-btn")
                yield ChoiceButton("No", id="no-begin-btn", classes="dialog-begin-btn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-begin-btn":
            self.app.push_screen(DownloadEvdiSoftwareScreen(
                displaylink_cl=self.displaylink_cl
            ))
        else:
            self.app.exit()


# EVDI Software Download Screen
class DownloadEvdiSoftwareScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Label(">>> Cloning the EVDI software driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_pull_evdi()

    @work(thread=True)
    def exec_pull_evdi(self) -> None:
        self.displaylink_cl.evdi_git_clone()
        self.app.call_from_thread(self.app.push_screen, EvdiDecisionScreen(
            displaylink_cl=self.displaylink_cl
        ))


# To-Do: EVDI List Screen
class EvdiDecisionScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self, 
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        self.evdi_git_gag_list = displaylink_cl.evdi_git_list_util()
        self.evdi_git_primary = displaylink_cl.find_git_primary()
        self.evdi_git_pull = displaylink_cl.evdi_pull_tag_util
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(EVDI_DEC_MESSAGE)
            yield ListView(
                # Keep for potential list
                # *[ListItem(Label(str(item))) for item in self.evdi_git_gag_list],
                ListItem(Label(f":: {self.evdi_git_gag_list[-1]} [bold]RECOMMENDED[/bold]"), id=f"{self.evdi_git_gag_list[-1].name.replace(".", "_")}"),
                ListItem(Label(f":: {self.evdi_git_primary.capitalize()} For Experimental Features. Use at own risk."), id=f"{self.evdi_git_primary}"),
            )
        yield Footer(id="Footer")

    @on(ListView.Selected)
    def handle_selection(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        self.process_selected_value(item_id)

    def process_selected_value(self, value: str | None) -> None:
        if value:
            self.evdi_git_pull(evdi_dec=value.replace("_", "."))
            self.app.push_screen(DisplayLinkDownloadScreen(
                displaylink_cl=self.displaylink_cl
            ))


# DisplayLink Software Download Screen
class DisplayLinkDownloadScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Label(">>> Downloading the latest Synaptics DisplayLink Driver.")
            yield LoadingIndicator()
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_download_display()

    @work(thread=True)
    def exec_download_display(self) -> None:
        self.displaylink_cl.download_displaylink()
        self.app.call_from_thread(self.app.push_screen, BeginDisplayLinkInstallDialogueScreen(
            displaylink_cl=self.displaylink_cl
        ))


# DisplayLink Software Install Screen
class BeginDisplayLinkInstallDialogueScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(INSTALL_DEC_MESSAGE)
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Yes", id="yes-install-btn", classes="dialog-install-btn")
                yield ChoiceButton("No", id="no-install-btn", classes="dialog-install-btn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-install-btn":
            self.app.push_screen(DisplayLinkInstallationScreen(
                displaylink_cl=self.displaylink_cl
            ))
        else:
            # Push to Clean Screen
            self.app.push_screen(CleanFilesExitScreen(
                displaylink_cl=self.displaylink_cl
            ))


# DisplayLink Install Functions Screen
class DisplayLinkInstallationScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(INSTALLATION_LOG_MESSAGE)
            yield RichLog(id="install-log", highlight=True, markup=True)
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_display_install()

    @work(thread=True)
    def exec_display_install(self) -> None:
        dispLog = self.query_one("#install-log", RichLog)

        for line in self.displaylink_cl.extract_displaylink_firmware():
            self.app.call_from_thread(dispLog.write, line)

        self.app.call_from_thread(self.app.push_screen, CleanFilesExitScreen(
            displaylink_cl=self.displaylink_cl
        ))


# Clean Files and Exit Screen
class CleanFilesExitScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Label(">>> Now removing all downloaded files and exiting.")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.exec_clean_files()

    @work(thread=True)
    def exec_clean_files(self) -> None:
        self.displaylink_cl.clean_files()
        self.app.call_from_thread(self.app.push_screen, FinalizeScreen(displaylink_cl=self.displaylink_cl))


# Finalize Screen 
class FinalizeScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        self.runit_test = self.displaylink_cl.runit_test()
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Static(EXIT_MESSAGE)
            if self.runit_test.stdout.strip() == "runit":
                yield Static(RUNIT_MESSAGE, id="finish-inst-message")
            else:
                yield Static(SYSTEMD_MESSAGE, id="finish-inst-message")
            yield Label(">>> Would you like the installer to handle these manual actions for you?")
            with Grid(id="horizontal-inst-btn"):
                yield ChoiceButton("Yes, Enable Service", id="yes-en-btn", classes="exit-inst-btn")
                yield ChoiceButton("No, Exit Installer", id="no-en-btn", classes="exit-inst-btn")
        yield Footer(id="Footer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-en-btn":
            self.app.push_screen(FinishExitScreen(displaylink_cl=self.displaylink_cl))
        else:
            self.app.exit()


# Finish and Exit Screen
class FinishExitScreen(Screen):
    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:

        self.displaylink_cl = displaylink_cl
        self.runit_test = self.displaylink_cl.runit_test()
        self.runit_prepare = self.displaylink_cl.runit_enable_display
        self.systemd_prepare = self.displaylink_cl.systemd_enable_display
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Header(id="Header")
        with Container(id="undisp-dialog"):
            yield Label(">>> Preparing your system...")
            with Grid(id="horizontal-ex-btn"):
                yield ChoiceButton("Exit the Installer", id="exit-button", classes="exit-inst-btn")
        yield Footer(id="Footer")

    def on_mount(self) -> None:
        self.prepare_system()

    @work(thread=True)
    def prepare_system(self) -> None:
        if self.runit_test.stdout.strip() == "runit":
            self.runit_prepare()
        else:
            self.systemd_prepare()
        self.app.call_from_thread(self.prepare_complete)

    def prepare_complete(self) -> None:
        exBtn = self.query_one("#exit-button", Button)
        exBtn.styles.display = "block"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit-button":
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

    CSS_PATH = Path(__file__).parent / "styles.tcss"

    def __init__(
        self,
        displaylink_cl,
        **kwargs
        ) -> None:
        
        self.displaylink_cl = displaylink_cl
        self.connect_test = displaylink_cl.connection_check()
        self.displaylink_install_check = displaylink_cl.displaylink_install_check()
        super().__init__(**kwargs)

    modal_result = reactive[bool | None](None)

    def on_mount(self) -> None:
        self.theme = "nord"

    def on_ready(self) -> None:
        self.push_screen(BeginInstallScreen(
            displaylink_cl=self.displaylink_cl
        ))
        if not self.connect_test:
            self.push_screen(NoConnectionModal(), self.handle_modal_result)

        if self.displaylink_install_check and self.connect_test:
            self.push_screen(InstallModal(), self.handle_modal_result)

    def handle_modal_result(self, result: bool | None) -> None:
        self.modal_result = result

    def watch_modal_result(self, old_value: bool | None, new_value: bool | None) -> None:
        if new_value is not None:
            if not new_value:
                self.exit()
            else:
                self.push_screen(UninstallDialogScreen(
                    displaylink_cl=self.displaylink_cl
                ))


if __name__ == "__main__":
    app = DisplayLinkInstaller(displaylink_cl=DispLink)
    app.run()
