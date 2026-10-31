## Quickstart:  

**Please Note:** This installer is only for Linux.   

1) Please download the ELF binary for your Linux Distro:  

    **PyDisplaylinkSynapticsInstall_<DISTRO>**  
  
<br>  

2) Install dependencies (if not already installed):  

- if any dependencies on these lists are missing, please create a [github issue](https://github.com/thompsonseanr/DisplayLink-EVDI-Install-Script/issues) and I will update the list for each respective distro.  
- `wget` is optional and only required for the bash script. It is only kept here now as a "good-to-have" now and moved to the end of the list for easy removal.

<br>

Void Linux:  

```
xbps-install -S xbps-install -S dkms libdrm libdrm-devel zstd pkg-config zip unzip wget
```

Fedora:  

```
dnf install dkms libdrm libdrm-devel kernel-devel kernel-headers zstd wget
```  

```
dnf group install development-tools
```  

Arch:    
```
pacman -S --needed base-devel linux-headers zstd libdrm dkms zip unzip wget
```

openSUSE Tumbleweed:  
```
zypper install -t pattern devel_basis
```
```
zypper install kernel-devel kernel-source libdrm-devel dkms
```
  
<br>  

3) Make `PyDisplaylinkSynapticsInstall_<DISTRO>` executable:  

```
chmod +x PyDisplaylinkSynapticsInstall_<DISTRO>
```

<br>  

4) Run installer as `sudo`:  

```
sudo ./PyDisplaylinkSynapticsInstall_<DISTRO>
```

<br>

5) **Optional** Add to path for future **EVDI** and/or **Synaptics DisplayLink Driver** updates. This TUI also runs uninstall wrapper scripts:

    - Copy executable to **/opt**    

    - Make symlink in `/usr/local/bin`:  
    ```
    sudo ln -s /opt/PyDisplaylinkSynapticsInstall_<DISTRO> /usr/local/bin/PyDisplaylinkSynapticsInstall_<DISTRO>
    ```