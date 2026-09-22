import os
import sys
import subprocess
import shutil
import git
import tarfile
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

initSearchDir: str = f"/home/{locUser}"
evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
# evdiDirFind: list[Path] = dir_find(initSearchDir, "evdi")
# evdiGitPath: Path | None = evdiDirFind[0] if evdiDirFind else None
evdiGitPath: Path = Path("/tmp/evdi")
# evdiTarPath: str | None = os.path.dirname(evdiGitPath) if evdiGitPath else None
evdiTarPath: str = os.path.dirname(evdiGitPath)
evdiGitMain: str | None
evdiGitTag: str | None

# Current DisplayLink Download: https://www.synaptics.com/sites/default/files/exe_files/2026-06/DisplayLink%20USB%20Graphics%20Software%20for%20Ubuntu6.3-EXE.zip
displayLinkDl: str | None
# This logic will change when executable is no longer called
displayLinkScraperFind: list[Path] = file_find(initSearchDir, "playwright_scraper")
displayLinkScraper: Path | None = displayLinkScraperFind[0] if displayLinkScraperFind else None
for scraper in displayLinkScraperFind:
    print(f"scraper: {scraper}")
displayStatus: str | None
displayLinkFullNameFind: list[Path] = file_find(initSearchDir, "DisplayLink*.zip")
displayLinkFullName: Path | None = displayLinkFullNameFind[0] if displayLinkScraperFind else None
displayLinkPath: str | None
displayLinkName: str | None
displayLinkNameFix: str | None
displayLinkVer: str | None
displayLinkTarget: str | None
displayLinkFileDir: Path | None
displayLinkInstallDir: Path | None
dispArr: list[Path] = file_find(initSearchDir, "DisplayLink*.zip")
dispArrVal: Path | None = dispArr[0] if dispArr else None
for displayVal in dispArr:
    print(f"displayVal: {displayVal}")
print(dispArrVal)
# Logic if len(dispArr) > 1
# Refactor and rethink

evdiTest: subprocess.CompletedProcess[str] = subprocess.run(f'lsmod | grep -Eio "evdi" | head -1', 
    shell=True, 
    capture_output=True, 
    text=True
)
displayInstallerTest: Path = Path("/usr/bin/displaylink-installer")
installDec: str = ""
print(f"lsmod: {evdiTest.stdout}")

downloadEvdiFile: bool = False
downloadDisplayFile: bool = False

# Test for DisplayLink
isDisplayLinkInstalled: bool = True if (evdiTest.stdout and displayInstallerTest.is_file()) else False

print(f"isDisplayLinkInstalled: {isDisplayLinkInstalled}")

def clean_files() -> None:
    # if downloadEvdiFile:
    if Path(f"{evdiTarPath}/evdi.tar.gz").is_file():
        try:
            os.remove(f"{evdiTarPath}/evdi.tar.gz")
        except FileNotFoundError:
            pass
    if evdiGitPath:
        try:
            shutil.rmtree(evdiGitPath)
        except FileNotFoundError:
            pass
    # if downloadDisplayFile:
    if displayLinkFullName:
        try:
            os.remove(displayLinkFullName)
        except FileNotFoundError:
            pass
    if displayLinkInstallDir and displayLinkInstallDir.is_dir():
        try:
            shutil.rmtree(displayLinkInstallDir)
        except FileNotFoundError:
            pass
    sys.exit(1)

def evdi_git_tag_util() -> None:
    global evdiGitPath
    global evdiDirFind
    global evdiTarPath
    global evdiGitMain
    global evdiGitTag

    # Change logic: do not look for /evdi in home, just clone it to /tmp/
    # Same for DisplayLinkManager. 
    if evdiGitPath.is_dir():
        with suppress(FileNotFoundError):
            shutil.rmtree("/tmp/evdi")
        with suppress(FileNotFoundError):
            os.remove("/tmp/evdi.tar.gz")
        
    Repo.clone_from(evdiRepo, "/tmp/evdi")

    evdiDirFind = dir_find("/tmp/", "evdi")
    evdiGitPath = evdiDirFind[0] if evdiDirFind else None
    evdiTarPath = os.path.dirname(evdiGitPath) if evdiGitPath else None

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

    print(f"evdiGitMain: {evdiGitMain}")

    evdiList: List[TagReference] = sorted(localEvdiRepo.tags, 
        key=lambda t: t.commit.committed_date, 
        reverse=True
    )

    if not evdiList:
        clean_files()

    # Create Dynamic menu for Textualize
    for tag in evdiList:
        print(tag.name, tag.commit.committed_datetime)

    # latest tag
    print(f"evdiList: {evdiList[0]}")

    evdiGitTag = evdiList[0]

    localEvdiOrigin.fetch(tags=True)
    localEvdiRepo.git.checkout("-b", evdiGitTag)

    with tarfile.open(f"{evdiTarPath}/evdi.tar.gz", "w:gz") as tarFile:
        tarFile.add(evdiGitPath, arcname=".")

    localEvdiRepo.git.checkout(evdiGitMain)
    localEvdiRepo.delete_head(evdiGitTag)

    

evdi_git_tag_util()

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