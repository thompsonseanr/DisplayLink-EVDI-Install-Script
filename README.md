# Linux Multi-Monitor DisplayLink Driver and EVDI Install Utility

> **Download Links:**  
> - [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  
> - [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  
>
> 
> **References and Attribution:**
> - [Textual](https://textual.textualize.io/)  
> - [uv](https://docs.astral.sh/uv/)  
> - [JBlond - Bash Colors](https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124)  
> - [Fix DisplayLink on Kernel 6.0 and up](https://mrk.sh/fix-displaylink-kernel6.0/)  
> - [Fixing DisplayLink (EVDI) drivers for Linux kernel 6.x](https://code.berrydejager.com/Fix-DisplayLink_drivers-linux-kernel-6/)  
> - [Porting the DisplayLink Ubuntu driver to other Linux distributions](https://support.displaylink.com/knowledgebase/articles/679060)  
> - [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781)  
> - [Reddit: DisplayLink Driver](https://www.reddit.com/r/voidlinux/comments/peq1se/displaylink_driver/)
> - [Alberta Tech - Hilarious Nerd Merch (I am not affiliated, just showing some love)](https://shop.albertatech.co/)  
> - [makeself - Make self-extractable archives on Unix](https://makeself.io/)  
>
>
> **Bugfixes and Contributions:**  
> - [edzweistein](https://github.com/edzweistein)  

<br>  

## Release Update:  

This was re-written in python with [Playwright](https://playwright.dev/) and the [Textual](https://textual.textualize.io/) TUI. The bash script [py_whl_build_install](#build-and-install-the-python-whl-with-py_whl_build_install) was written to build and install or uninstall the .whl using [uv](https://docs.astral.sh/uv/) python package manager.  

<br>

**IMPORTANT:** If you used the [py_whl_build_install](#build-and-install-the-python-whl-with-py_whl_build_install) to build and install the .whl, the main DisplayLink executable is now: 

```
displaylink_install_tui
```

<br>

The original [shell script](#bash-script) is an option, but will no longer be actively updated with new features outside of periodically updating the **Synaptics DisplayLink Driver** download url.  

<br>  

The python executable will still require build dependencies to be installed. Directions for how to create your own package locally without using the are in the python module: [Linux Multi-Monitor DisplayLink Driver and EVDI Install Utility Local Python Wheel Build Instructions](py_displaylink_synaptics_install/README.md).  
  
There are still improvements to be made (dependency checks with warnings), so new releases will be coming.  

## Preface:  

If after a kernel update your DisplayLink and EVDI module breaks, you can use this script to update to the latest version of the EVDI driver. Using this script will hopefully keep you from workarounds like kernel version pinning.  

If you installed **EVDI** and **DisplayLink** drivers via you package manager, please uninstall them before proceeding.  

Due to an issue encountered with an older, incompatible version of **EVDI** and the latest **Linux 7.X.X** kernel, this script was written to decouple the version of the **EVDI** module bundled with the [Synaptics DisplayLink Driver and Manager](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu) installer and give users the option to choose the version of **EVDI** from the [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi) that works for their kernel version.

You will need to disable **Secure Boot** in your bios.  

I want to give a huge shout-out, thanks, and appreciation for the developers and maintainers of the following repos and packages:  
| Distros | Repo/Package |
| :--- | :--- |
| Arch | [evdi-dkms](https://aur.archlinux.org/packages/evdi-dkms) |
| Arch | [displaylink](https://aur.archlinux.org/packages/displaylink) |
| Fedora | [displaylink-rpm](https://github.com/displaylink-rpm/displaylink-rpm) |  
| Fedora | [Negativo17](https://negativo17.org/repos/fedora-multimedia) |


This script is a fun, straightforward, and old-school [no vibes&trade;](https://shop.albertatech.co/products/anti-vibe-coder-coder-club-tee) solution.   

| Successful Distros | Notes |
| :--- | :--- |
| **Void** | TUI: Working without user interventions/solutions. Option created to handle required `runit` service interventions. Bash Script: You Will have to remove `down` service file from `/var/service/displaylink-driver/`. Restart the the `displaylink-driver` service. |   
| **Fedora 44** | Working without user interventions/solutions. |
| **Arch** |  Working without user interventions/solutions. |
| **openSUSE Tumbleweed** | May have to run: `systemctl restart displaylink-driver.service` after login or solutions such as manually unplugging and re-plugging in the docking station connection or turning it off/on. Found the issue running `journalctl -p 3 -xb` and it is related to the failed running of the shell script `/opt/displaylink/udev.sh`. Tried making the script executable, but that did not resolve the issue. For research purposes, the `udev` rule is: `/usr/lib/udev/rules.d/99-displaylink.rules`. Reference: [systemctl enable displaylink.service](https://github.com/displaylink-rpm/displaylink-rpm/issues/50) |

| **Features** | |
| :--- | :--- |
| Software Downloads: | If you do not have **DisplayLink Driver** or the git **EVDI** repo cloned, this script will download them for you. |
| EVDI Version Tag Menu: | Menu to choose which version of **EVDI** you want to install. |  
 
 <br>  

# Quickstart:  

**First, Please Install the Required Build Dependencies for Synaptics DisplayLink:**   

- if any dependencies on these lists are missing, please create a [github issue](https://github.com/thompsonseanr/DisplayLink-EVDI-Install-Script/issues) and I will update the list for each respective distro.  
- `wget` is optional and only required for the [bash script](#bash-script). It is only kept here as a "good-to-have" now and moved to the end of the list for easy removal.  

**Void Linux**: 
```
xbps-install -S xbps-install -S dkms libdrm libdrm-devel zstd pkg-config zip unzip wget
```
**Fedora 44:**    
```
dnf install dkms libdrm libdrm-devel kernel-devel kernel-headers zstd wget
```
```
dnf group install development-tools
```
**Arch:**  
```
pacman -S --needed base-devel linux-headers zstd libdrm dkms zip unzip wget
```
**openSUSE Tumbleweed:**
```
zypper install -t pattern devel_basis
```
```
zypper install kernel-devel kernel-source libdrm-devel dkms
```

<br>

## Build and install the python .whl with **py_whl_build_install**:

**Install Instructions:**  

1) Make the `py_whl_build_install` script executable:  

    ```
    chmod +x py_whl_build_install
    ```

2) .whl install as uv tool:  

    ```
    ./py_whl_build_install
    ```

3) Restart your shell (bash, zsh, etc.):  

    Bash:  

    ```
    source ~/.bashrc
    ```

    Zsh:  

    ```
    source ~/.zshrc
    ```

3) Run **displaylink_install_tui** to install the DisplayLink and EVDI module:  

    ```
    displaylink_install_tui
    ```


**Uninstallation of python .whl:**  

1) Run:  

    ```
    ./py_whl_build_install uninstall
    ```

<br>

## Bash Script

The script, by default, will look for **DisplayLink Manager** and **EVDI** anywhere in the **$USER** home directory and download them, if required.

**Instructions:**

1) Clone the repo.  
2) Make `displaylink_synaptics_install` executable:  
    ```
    chmod +x displaylink_synaptics_install
    ```
3) Make sure your build dependencies are installed.  

4) Run:  
    ```
    ./displaylink_synaptics_install
    ```

**To uninstall DisplayLink:**
> This is recommended if you are updating and will have to be done manually.

```
sudo displaylink-installer uninstall
```


