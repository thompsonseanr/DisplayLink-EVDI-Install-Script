# DisplayLink Manager and EVDI Install for Void

> **Links:**  
> [Fix DisplayLink on Kernel 6.0 and up](https://mrk.sh/fix-displaylink-kernel6.0/)  
> [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  
> [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  
> [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781)  

## Quickstart:

**UPDATE:** If you do not have `DisplayLink Driver` or the git `EVDI` repo cloned, this script will download them for you. 

1) Clone: [DisplayLink EVDI Git Repo](https://github.com/DisplayLink/evdi)  

2) Download: [Synaptics DisplayLink Driver and Manager Downloads](https://www.synaptics.com/products/displaylink-graphics/downloads/ubuntu)  

3) **Void Linux**: Install dependencies (UPDATED LIST):
    ```
    xbps-install -S xbps-install -S dkms libdrm libdrm-devel zstd pkg-config
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
4) Reload your terminal environment and run. You will need to make sure your build dependencies are installed. 

    Thank you: [Synaptics DisplayLink with evdi DKMS Module - Works!](https://voidforums.com/viewtopic.php?t=1781) 

    ```
    xbps-install -S dkms libdrm libdrm-devel zstd pkg-config
    ```

### To uninstall DisplayLink:

```
sudo displaylink-installer uninstall
```
