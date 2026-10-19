# Quickstart:  

**Please Note:** This installer is meant only for Linux.  

1) **Please download:** `py_displaylink_synaptics_install`  
  
<br>  

2) Install dependencies (if not already installed):  

<br>

- if any dependencies on these lists are missing, please create a `github issue` and I will update the list for each respective distro.  

<br>

**Void Linux:**  

```
xbps-install -S xbps-install -S dkms libdrm libdrm-devel zstd pkg-config wget zip unzip
```

**Fedora:**  

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
  
<br>  

3) Make `py_displaylink_synaptics_install` executable:  

```
chmod +x py_displaylink_synaptics_install
```
  
<br>  

4) Run installer as `sudo`:  

```
sudo ./py_displaylink_synaptics_install
```