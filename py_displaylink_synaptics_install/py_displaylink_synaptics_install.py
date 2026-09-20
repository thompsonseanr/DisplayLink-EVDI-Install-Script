import os
import subprocess
from pathlib import Path
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Welcome, Label, Button

# Personal Dev Notes: 
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

locUser: str | None = os.getenv('USER')
runitTest: subprocess.CompletedProcess[str] = subprocess.run("ps -p 1 -o comm=", shell=True, capture_output=True, text=True)

initSearchDir: str = f"/home/{locUser}"
evdiRepo: str = "https://github.com/DisplayLink/evdi.git"
evdiDirFind: list[Path] = dir_find(initSearchDir, "evdi")
evdiGitPath: Path | None = evdiDirFind[0] if evdiDirFind else None
evdiTarPath: str | None = os.path.dirname(evdiGitPath) if evdiGitPath else None
evdiGitMain: str | None = ""
evdiGitTag: str | None = ""

# Current DisplayLink Download: https://www.synaptics.com/sites/default/files/exe_files/2026-06/DisplayLink%20USB%20Graphics%20Software%20for%20Ubuntu6.3-EXE.zip
displayLinkDl: str | None = ""
displayLinkScraperFind: list[Path] = file_find(initSearchDir, "playwright_scraper")
displayLinkScraper: Path | None = displayLinkScraperFind[0] if displayLinkScraperFind else None
for scraper in displayLinkScraperFind:
    print(f"scraper: {scraper}")
displayStatus: str | None = ""
displayLinkFullName: str | None = ""
displayLinkPath: str | None = ""
displayLinkName: str | None = ""
displayLinkNameFix: str | None = ""
displayLinkVer: str | None = ""
displayLinkTarget: str | None = ""
displayLinkFileDir: str | None = ""
displayLinkInstallDir: str | None = ""
dispArr: list[Path] = file_find(initSearchDir, "DisplayLink*.zip")
dispArrVal: Path | None = dispArr[0] if dispArr else None
for displayVal in dispArr:
    print(f"displayVal: {displayVal}")
print(dispArrVal)

evdiTest: subprocess.CompletedProcess[str] = subprocess.run(f'lsmod | grep -Eio "evdi" | head -1', shell=True, capture_output=True, text=True)
displayInstallerTest: str = "/usr/bin/displaylink-installer"
installDec: str = ""
print(f"lsmod: {evdiTest.stdout}")

downloadEvdiFile: str = "false"
downloadDisplayFile: str = "false"




class QuestionApp(App[str]):
    def on_mount(self) -> None:
        self.theme = "nord"
    def compose(self) -> ComposeResult:
        yield Label(":::::::::::::::::::::::::::::::::::::::::::")
        yield Label("::: DisplayLink Installer")
        yield Label(":::::::::::::::::::::::::::::::::::::::::::")
        yield Button("Yes", id="yes", variant="primary") 
        yield Button("No", id="no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit(event.button.id)

if __name__ == "__main__":
    app = QuestionApp()
    reply = app.run()
    print(reply)
    # app.run()