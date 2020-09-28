Zephyr code examples
===
How to build:
---
* Follow the setup steps outlined [in this guide](https://docs.zephyrproject.org/latest/getting_started/index.html) to set up the Zephyr build environment.
  * I used a blank Debian (Buster) VM
* Run `west build -b <board_name> [-d path/to/build_dir] -t rom_report path/to/project`

```
# BLE peripheral
west build -p auto -b rv32m1_vega_ri5cy -d build_rv32_periph -t rom_report samples/bluetooth/peripheral
west build -p auto -b nrf52840dk_nrf52840 -d build_nrf52_periph -t rom_report samples/bluetooth/peripheral
west build -p auto -b nrf5340dk_nrf5340_cpunet -d build_nrf53_periph -t rom_report samples/bluetooth/peripheral
# BLE central
west build -p auto -b rv32m1_vega_ri5cy -d build_rv32_central -t rom_report samples/bluetooth/central
west build -p auto -b nrf5340dk_nrf5340_cpunet -d build_nrf53_central -t rom_report samples/bluetooth/central
west build -p auto -b nrf52840dk_nrf52840 -d build_nrf52_central -t rom_report samples/bluetooth/central
# BLE sensor
west build -p auto -b rv32m1_vega_ri5cy -d build_rv32_beacon -t rom_report samples/bluetooth/st_ble_sensor/
west build -p auto -b nrf52840dk_nrf52840 -d build_nrf52_st_sensor -t rom_report samples/bluetooth/st_ble_sensor/
west build -p auto -b nrf5340dk_nrf5340_cpunet -d build_nrf53_st_sensor -t rom_report samples/bluetooth/st_ble_sensor/
```

Results:
---
Zephyr version: 2.4.0-rc3 (SDK 0.11.4)  
Compiler: GCC 9.2.0

FLAGS (common) = `-Os -ffreestanding -fno-common -g -fno-asynchronous-unwind-tables -fno-pie -fno-pic -fno-strict-overflow -fno-reorder-functions -fno-defer-pop -ffunction-sections -fdata-sections -std=c99 -nostdinc`  
FLAGS (RV32)    = `-march=rv32imcxpulp -mabi=ilp32`  
FLAGS (ARMv7-M) = `-mcpu=cortex-m4 -mthumb -mabi=aapcs`  
FLAGS (ARMv8-M) = `-mcpu=cortex-m33+nodsp -mthumb -mabi=aapcs`  

| Benchmark      | RV32IMCXpulp \(VEGAboard, ri5cy\) | ARMv7\-M \(nRF52840\)         | ARMv8\-M \(nRF5340\_network\) |
|----------------|-----------------------------------|-------------------------------|-------------------------------|
| BLE peripheral | 206kB ROM / 25kB RAM              | 156kB (75.5%) / 26kB (104.4%) | 153kB (74.4%) / 24kB (97.9%)  |
| BLE central    | 147kB ROM / 17kB RAM              | 107kB (73.2%) / 18kB (106.2%) | 111kB (75.6%) / 18kB (105.7%) |
| BLE sensor     | 168kB ROM / 20kB RAM              | 124kB (73.8%) / 21kB (105.3%) | 126kB (75.4%) / 21kB (104.5%) |

For more details, see spreadsheet: *[Zephyr_size_comparison.ods](Zephyr_size_comparison.ods)*
