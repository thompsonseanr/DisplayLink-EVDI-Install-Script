# Linux Multi-Monitor DisplayLink Driver and EVDI Install Utility Local Python Wheel Build Instructions

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
  
## Building and Installing Python Wheel Locally with **uv**

1) Install [uv](https://docs.astral.sh/uv/getting-started/installation/):  

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
<br>  

2) Enter **python** module:  

```
cd py_displaylink_synaptics_install/
```  
<br>  

3) Create **venv**:

```
uv venv --python 3.14 
```
<br>  

4) Activate **venv**:

```
source .venv/bin/activate
```
<br>  

5) Install packages:  

```
uv sync
```

6) Install **Chromium** for **Playwright** for elevated user:
- There is now an option in the installer to install the Chromium driver, but will only work in an active virtual environment.

```
sudo env "PATH=$PATH" playwright install chromium
```
<br>  

7) Build **.whl**:

```
uv build --wheel
```
<br>  

8) Install created wheel from **/dist**:  

```
uv tool install dist/py_displaylink_synaptics_install-<VERSION>-py3-none-any.whl
```
<br>  

9) Run the installed wheel:  
- **Note:** this will have to run as `sudo` and disclaimer and reasons given in intro message.  
  

> **Disclaimer Message:**     
> Please run this script with `sudo`.  
> Elevated permissions are required for running the extracted DisplayLink displaylink-installer.sh script,  
> which builds the EVDI DKMS module, etc.  
> Exiting.

```
sudo env "PATH=$PATH" py_displaylink_synaptics_install 
```

or  

```
sudo /home/<USER>/.local/bin/py_displaylink_synaptics_install
```
