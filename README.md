# Linux Multi-Monitor DisplayLink Driver and EVDI Install Utility Shell Script

> **Download Links:**  
> - [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  
> - [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  
>
> 
> **References and Attribution:**
> - [JBlond - Bash Colors](https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124)  
> - [Fix DisplayLink on Kernel 6.0 and up](https://mrk.sh/fix-displaylink-kernel6.0/)  
> - [Fixing DisplayLink (EVDI) drivers for Linux kernel 6.x](https://code.berrydejager.com/Fix-DisplayLink_drivers-linux-kernel-6/)  
> - [Porting the DisplayLink Ubuntu driver to other Linux distributions](https://support.displaylink.com/knowledgebase/articles/679060)  
> - [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781)  
> - [Reddit: DisplayLink Driver](https://www.reddit.com/r/voidlinux/comments/peq1se/displaylink_driver/)
> - [Alberta Tech - Hilarious Merch (I am not affiliated, just a fan)](https://shop.albertatech.co/)  


## Preface:  

Due to an issue encountered with an older version of `EVDI 14.5.0` and the latest `Linux 7.X.X` kernel, this script was written to decouple the version of the `EVDI` module bundled with the [Synaptics DisplayLink Driver and Manager](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu) installer and give users the option to choose the version of `EVDI` from the [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi) that works for their system.  

You will need to disable `Secure Boot` in your bios.

I want to give a huge shout-out, thanks, and appreciation for the developers and maintainers of the following repos and packages:  
| Distros | Repo/Package |
| :--- | :--- |
| Arch | [evdi-dkms](https://aur.archlinux.org/packages/evdi-dkms) |
| Arch | [displaylink](https://aur.archlinux.org/packages/displaylink) |
| Fedora | [displaylink-rpm](https://github.com/displaylink-rpm/displaylink-rpm) |  
| Fedora | [Negativo17](https://negativo17.org/repos/fedora-multimedia) |


This script is a straightforward and old-school [no vibes&trade;](https://shop.albertatech.co/products/anti-vibe-coder-coder-club-tee) solution.  

| Successful Distros | Notes |
| :--- | :--- |
| **Void** | Have to remove `down` service file from `/var/service/displaylink-driver/`. Restart the the `displaylink-driver` service. |   
| **Fedora 44** | Working without user interventions/solutions. |
| **Arch** |  Working without user interventions/solutions. |
| **openSUSE Tumbleweed** | May have to run: `systemctl restart displaylink-driver.service` after login or the technical solutions of manually unplugging and re-plugging in the docking station connection or turning it off/on. I vaguely remember experiencing this in `Arch` years ago and think I ran a script from a post-login triggered systemd unit that was essentially a displaylink-driver service restart hook. The solution is most likely related to the `usb` device instantiation not registering correctly and the solution is out of scope of this script. Tried blacklisting `udl` and `udlfb` drivers to no avail. Reference: [HowTo build Displaylink driver for OpenSuse Tumbleweed with latest kernel](https://0xcaffee.blog/posts/opensuse-tumbleweed-evdi/). For research purposes, the `udev` rule is: `/usr/lib/udev/rules.d/99-displaylink.rules`. Reference: [systemctl enable displaylink.service](https://github.com/displaylink-rpm/displaylink-rpm/issues/50) |

| **Features** | |
| :--- | :--- |
| Software Downloads: | If you do not have `DisplayLink Driver` or the git `EVDI` repo cloned, this script will download them for you. |
| EVDI Version Tag Menu: | Menu to choose which version of `EVDI` you want to install. |
| **Bring Your Own Software** DisplayLink Install Menu: | Menu to choose which local version of `DisplayLink` you want to install if you decided to live the `BYOS` lifestyle. |
 

## Quickstart:  

The script, by default, will look for `DisplayLink Manager` and `EVDI` anywhere in the `$USER` home directory.

1) **[Optional]** Clone: [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  

2) **[Optional]** Download: [Synaptics DisplayLink Driver and Manager Downloads - Latest Official Driver - DisplayLink USB Graphics Software for Ubuntu](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  

3) Install dependencies:  

    - if any are missing, please create a `github issue` and I will update the list for each respective distro.  

    **Void Linux**: 
    ```
    xbps-install -S xbps-install -S dkms libdrm libdrm-devel zstd pkg-config wget zip unzip
    ```
    **Fedora 44:**    
    ```
    dnf install dkms libdrm libdrm-devel kernel-devel kernel-headers wget zstd
    ```
    ```
    dnf group install development-tools
    ```
    **Arch:**  
    ```
    pacman -S --needed base-devel linux-headers wget zstd libdrm dkms zip unzip
    ```
    **openSUSE Tumbleweed:**
    ```
    zypper install -t pattern devel_basis
    ```
    ```
    zypper install kernel-devel kernel-source libdrm-devel dkms
    ```

### Run the `displaylink_synaptics_install` script:

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

### To uninstall DisplayLink:
> This is recommended if you are updating and will have to be done manually.

```
sudo displaylink-installer uninstall
```
