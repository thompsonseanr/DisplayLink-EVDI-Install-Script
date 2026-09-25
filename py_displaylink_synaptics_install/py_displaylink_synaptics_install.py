import os
import sys
import subprocess
import shutil
import git
import tarfile
import zipfile
import re
import py_playwright_scraper
from contextlib import suppress
from pathlib import Path
from typing import List
from git import Repo
from git import TagReference
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, RichLog, Welcome, Label, Button

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

def dir_find(initSearchDir: str, targetObj: str) -> list[Path]:
    return [d for d in Path(initSearchDir).rglob(targetObj) if d.is_dir()]

def file_find(initSearchDir: str, targetObj: str) -> list[Path]:
    return [f for f in Path(initSearchDir).rglob(targetObj) if f.is_file()]

locUser: str | None = os.getenv('USER') if os.getenv('USER') else None
runitTest: subprocess.CompletedProcess[str] = subprocess.run("ps -p 1 -o comm=", 
    shell=True, 
    capture_output=True, 
    text=True
)

initTmpDir: str = "/tmp/"
evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
evdiGitPath: Path = Path("/tmp/evdi")
evdiTarPath: str = os.path.dirname(evdiGitPath)
evdiGitMain: str | None
evdiGitTag: str | None

# Current DisplayLink Download: https://www.synaptics.com/sites/default/files/exe_files/2026-06/DisplayLink%20USB%20Graphics%20Software%20for%20Ubuntu6.3-EXE.zip
py_playwright_scraper.py_scraper()
displayLinkFullNameFind: list[Path] = file_find(initTmpDir, "DisplayLink*.zip")
displayLinkFullName: Path | None = displayLinkFullNameFind[0] if displayLinkFullNameFind else None
if not displayLinkFullName:
    sys.exit(1)
else:
    displayLinkPath: Path = displayLinkFullName.parent
    displayLinkName: str = displayLinkFullName.name
    displayLinkNameFix: Path = displayLinkFullName.parent / displayLinkFullName.name.replace(" ", "_")
    displayLinkFullNameUp: Path = displayLinkFullName.rename(displayLinkNameFix)
    displayLinkVer: List[str] = re.findall(r"\d+\.\d+", displayLinkFullNameUp.name)
    displayLinkTarget: str = f"displaylink_{displayLinkVer[0]}"
    displayLinkFileDir: Path = displayLinkFullName.parent / displayLinkTarget
    displayLinkInstallDir: Path = Path(f"/opt/{displayLinkTarget}")

evdiTest: subprocess.CompletedProcess[str] = subprocess.run(f'lsmod | grep -Eio "evdi" | head -1', 
    shell=True, 
    capture_output=True, 
    text=True
)
displayInstallerTest: Path = Path("/usr/bin/displaylink-installer")
installDec: str
print(f"lsmod: {evdiTest.stdout}")

# Test for DisplayLink
isDisplayLinkInstalled: bool = True if (evdiTest.stdout and displayInstallerTest.is_file()) else False

print(f"isDisplayLinkInstalled: {isDisplayLinkInstalled}")

def clean_files() -> None:
    if Path(f"{evdiTarPath}/evdi.tar.gz").is_file():
        with suppress(FileNotFoundError):
            os.remove(f"{evdiTarPath}/evdi.tar.gz")
    if evdiGitPath:
        with suppress(FileNotFoundError):
            shutil.rmtree(evdiGitPath)
    if displayLinkFullNameUp:
        with suppress(FileNotFoundError):
            os.remove(displayLinkFullNameUp)
    if displayLinkInstallDir and displayLinkInstallDir.is_dir():
        with suppress(FileNotFoundError):
            subprocess.run(["sudo", "rm", "-rf", displayLinkInstallDir], check=True)
    sys.exit(1)

def evdi_git_tag_util() -> None:
    global evdiGitPath
    global evdiTarPath
    global evdiGitMain
    global evdiGitTag

    if evdiGitPath.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree("/tmp/evdi")
        with suppress(FileNotFoundError):
            os.remove("/tmp/evdi.tar.gz")
        
    Repo.clone_from(evdiRepo, "/tmp/evdi")

    if evdiGitPath is None: 
        sys.exit(1)
    elif not evdiGitPath.is_dir():
        sys.exit(1)

    os.chdir(evdiGitPath)
    localEvdiRepo: git.repo.base.Repo = git.Repo(evdiGitPath)
    localEvdiOrigin: git.remote.Remote = localEvdiRepo.remotes.origin
    localEvdiOrigin.pull()
    evdiGitMainFind: subprocess.CompletedProcess[str] = subprocess.run("git rev-parse --abbrev-ref origin/HEAD | cut -d/ -f2", 
        shell=True, 
        capture_output=True, 
        text=True
    )
    evdiGitMain = evdiGitMainFind.stdout.strip()

    evdiList: List[TagReference] = sorted(localEvdiRepo.tags, 
        key=lambda t: t.commit.committed_date, 
        reverse=True
    )

    if not evdiList:
        clean_files()

    # Create Dynamic menu for Textualize
    for tag in evdiList:
        print(tag.name, tag.commit.committed_datetime)

    # latest tag - placeholder
    print(f"evdiList: {evdiList[0]}")
    evdiGitTag = evdiList[0]

    localEvdiOrigin.fetch(tags=True)
    localEvdiRepo.git.checkout("-b", evdiGitTag)

    with tarfile.open(f"{evdiTarPath}/evdi.tar.gz", "w:gz") as tarFile:
        tarFile.add(evdiGitPath, arcname=".")

    localEvdiRepo.git.checkout(evdiGitMain)
    localEvdiRepo.delete_head(evdiGitTag)

    
def unzip_displaylink() -> None:
    with zipfile.ZipFile(displayLinkFullNameUp, 'r') as zipRef:
        zipRef.extractall(displayLinkFileDir)


def install_dir_rename() -> None:
    subprocess.run(["sudo", "mv", displayLinkFileDir, displayLinkInstallDir], check=True)
    subprocess.run(["sudo", "chown", "-R", f"{locUser}:{locUser}", displayLinkInstallDir], check=True)
    os.chdir(displayLinkInstallDir)

def extract_displaylink_firmware() -> None:
    runFileFind: list[Path] = file_find(displayLinkInstallDir, "*.run")
    print(runFileFind[0])
    runFile: Path | None = runFileFind[0] if runFileFind else None
    if runFile:
        subprocess.run(["sudo", "chmod", "+x", runFile], check=True)
        try:
            subprocess.run(["sudo", runFile, "--noexec", "--keep"], check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                os.chdir("/opt")
                clean_files()
        subprocess.run(["sudo", "chown", "-R", f"{locUser}:{locUser}", displayLinkInstallDir], check=True)
        extractDirFind: list[Path] = dir_find(displayLinkInstallDir, "displaylink-*")
        extractDir: Path | None = extractDirFind[0] if extractDirFind else None
        os.chdir(extractDir)
        os.remove("evdi.tar.gz")
        shutil.move(f"{evdiTarPath}/evdi.tar.gz", extractDir)
        subprocess.run(["sudo", "chown", "-R", f"{locUser}:{locUser}", displayLinkInstallDir], check=True)
        subprocess.run(["sudo", "chmod", "+x", f"{extractDir}/displaylink-installer.sh"], check=True)
        subprocess.run(["sudo", "./displaylink-installer.sh", "noreboot"], check=True)


# Menu to capture evdi decision, then do the remaining operations
evdi_git_tag_util()
unzip_displaylink()
install_dir_rename()
extract_displaylink_firmware()
clean_files()


# class DisplayLinkInstall(App):
#     BINDINGS = [
#         Binding(key="q", action="quit", description="Quit the DisplayLink Installer")
#     ]
#     def on_mount(self) -> None:
#         self.theme = "nord"
#     def compose(self) -> ComposeResult:
#         yield Header()
#         yield Label(":::::::::::::::::::::::::::::::::::::::::::")
#         yield Label("::: DisplayLink Installer")
#         yield Label(":::::::::::::::::::::::::::::::::::::::::::")
#         yield Button("Start", id="start", variant="primary") 
#         # yield Button("No", id="no", variant="error")
#         yield Footer()

#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         self.exit(event.button.id)

#     evdi_git_tag_util()

# if __name__ == "__main__":
#     app = DisplayLinkInstall()
#     reply = app.run()
#     print(reply)
#     # app.run()