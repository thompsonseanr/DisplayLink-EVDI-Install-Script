## Quickstart:  

**Please Note:** This installer is only for Linux.   

1) Please download the python wheel:  

    **py_displaylink_synaptics_install-<VERSION>-py3-none-any.whl**  
  
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

3) Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
<br>  

4) Install downloaded **.whl**:  

```
uv tool install py_displaylink_synaptics_install-<VERSION>-py3-none-any.whl
```

5) Run the installed wheel. **Note:** this will have to run as `sudo` and disclaimer and reasons given in intro message:  
  

> **Disclaimer Message:**     
> Please run this script with `sudo`.  
> Elevated permissions are required for running the extracted DisplayLink displaylink-installer.sh script,  
> which builds the EVDI DKMS module, etc.  
> Exiting.

  
```
sudo /home/<USER>/.local/bin/py_displaylink_synaptics_install
```

or

```
sudo env "PATH=$PATH" py_displaylink_synaptics_install 
```