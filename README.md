# DisplayLink Manager and EVDI Install for Void

> **Links:**  
> [Fix DisplayLink on Kernel 6.0 and up](https://mrk.sh/fix-displaylink-kernel6.0/)  
> [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  
> [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  
> [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781)  

## Quickstart:

**Important**:

1) Clone: [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  

2) Download: [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  

3) **Void Linux**: Install dependencies:
    ```
    xbps-install -S dkms libdrm libdrm-devel zstd elgoind sddm kde-plasma xorg-minimal xf86-video-intel pkg-config
    ```

### Run the `displaylink_synaptics_install` script:

Due to an issue encountered with an older version of `EVDI 14.5.0` and the latest `Linux 7.xx` kernel, this script was written to update the version of `EVDI` from the [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi) and use that version for the [Synaptics DisplayLink Driver and Manager](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  

**Instructions:**

1) Clone the repo.  
2) Move `displaylink_synaptics_install` to `/usr/local/bin`  
3) Make it executable:  
    ```
    chmod +x displaylink_synaptics_install
    ```
4) Reload your terminal environment and run. You will need to make sure your build dependencies are installed. Thank you: [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781) 

    ```
    xbps-install -S dkms libdrm libdrm-devel zstd elgoind sddm kde-plasma xorg-minimal xf86-video-intel pkg-config
    ```


# Personal Notes Section:  

### Git Commands for EVDI Repo:

- Git pull latest tag:  

```
git fetch --tags
```
```
git describe --tags $(git rev-list --tags --max-count=1)
```

- Create branch from latest tag:  

```
git fetch --tags && git checkout -b $(git describe --tags $(git rev-list --tags --max-count=1))
```

- Tar.gz latest tag:  

```
tar -czvf evdi.tar.gz -C /path/to/<EVDI_REPO> .
```

```
tar -czvf ../evdi.tar.gz .
```

### Tar.gz Commands for EVDI:  

- To tar a directory's contents:  

```
tar -czvf <ARCHIVE_NAME>.tar.gz -C /path/to/folder .
```

- To untar an archive:  

```
tar -xf <ARCHIVE_NAME>.tar.gz -C /path/to/<TARGET_FOLDER>
```

### Unzip Commands for DisplayLink (/opt/):  

```
sudo unzip <DisplayLink_VERSION>.zip -d displaylink_<VERSION>
```
```
sudo unzip DisplayLink\ USB\ Graphics\ Software\ for\ Ubuntu6.3-EXE.zip -d displaylink_6.3
```

### Extract DisplayLink Installer from Run Script:  

```
sudo ./displaylink-driver-6.3.0-48.run --noexec --keep
```

### Move into Extracted Directory  

```
sudo chown -R $USER:$USER <EXTRACTED_DISPLAYLINK_INSTALLER_DIRECTORY>
```

```
cd <EXTRACTED_DISPLAYLINK_INSTALLER_DIRECTORY>
```

### Copy Created `evdi.tar.gz` to Extracted Directory  

```
mv evdi.tar.gz evdi.tar.gz.bak.$(date +%Y%m%d)
```

```
mv /path/to/git/evdi.tar.gz .
```

```
rm -f evdi.tar.gz.bak.*
```

### Run `displaylink-installer.sh`  

```
sudo ./displaylink-installer.sh
```

## Post-installation for `runit` hipsters:

Disable the `down` service file in `/var/service/displaylink-driver`  

```
cd /var/service/displaylink-driver
```
```
sudo mv down down.bak.$(date +%Y%m%d)
```
```
sudo sv restart displaylink-driver
```
