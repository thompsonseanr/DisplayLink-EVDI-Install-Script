# Linux Multi-Monitor DisplayLink Driver and EVDI Install Utility

> **Download Links:**  
> - [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  
> - [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  
>
> 
> **References and Attribution:**
> - [Textual](https://textual.textualize.io/)  
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

## Preface:  

Due to an issue encountered with an older, incompatible version of **EVDI** and the latest **Linux 7.X.X** kernel, this script was written to decouple the version of the **EVDI** module bundled with the [Synaptics DisplayLink Driver and Manager](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu) installer and give users the option to choose the version of **EVDI** from the [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi) that works for their kernel version.

You will need to disable **Secure Boot** in your bios.  

If you installed **EVDI** and **DisplayLink** drivers via you package manager, please uninstall them before proceeding.  

I want to give a huge shout-out, thanks, and appreciation for the developers and maintainers of the following repos and packages:  
| Distros | Repo/Package |
| :--- | :--- |
| Arch | [evdi-dkms](https://aur.archlinux.org/packages/evdi-dkms) |
| Arch | [displaylink](https://aur.archlinux.org/packages/displaylink) |
| Fedora | [displaylink-rpm](https://github.com/displaylink-rpm/displaylink-rpm) |  
| Fedora | [Negativo17](https://negativo17.org/repos/fedora-multimedia) |  

  

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
  
## Building and Installing Python Wheel Locally with Pip

1) Build wheel:  

```
python -m build
```

2) Install created wheel from **/dist**:  

```
pip install dist/py_displaylink_synaptics_install-<VERSION>-py3-none-any.whl
```

3) Run the installed wheel. **Note:** this will have to run as `sudo` and disclaimer and reasons given in intro message:  
  

> **Disclaimer Message:**     
> Please run this script with `sudo`.  
> Elevated permissions are required for running the extracted DisplayLink displaylink-installer.sh script,  
> which builds the EVDI DKMS module, etc.  
> Exiting.

```
sudo py_displaylink_synaptics_install
```