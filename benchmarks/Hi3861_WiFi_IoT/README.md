Hi3861 Huawei WiFi Iot SDK
---------------------------

[On this page](https://device.harmonyos.com/en/docs/start/get-code/oem_sourcecode_guide-0000001050769927) click on full code base/site to download this file:

[Download this file](https://repo.huaweicloud.com/harmonyos/os/1.0/code-1.0.tar.gz)

You can download HCC [here](https://gitee.com/hihopeorg/gcc_compiler_riscv)

HCC has support for the [Huawei Custom ISA extension](https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/README.md)

You can compile with GCC or HCC (or other compilers presumably, but we haven't tried that).

1.	Put the compiler you wish to use in a directory called gcc_riscv32, and add the bin subdirectory of the compiler to the PATH variable
-	We tried this with GCC10

2.	Install any version of scons newer than 3.0.1 and install any version of python newer than 3.7 
3.	Change the following files:
-	build/scripts/scons_env_cfg.py: Line 82: self.gcc_ver_num = 'x.x.x' -> to the compiler version used
-	vendor/hisi/hi3861/hi3861/build/link/link.ld.S: Line 78: Change ROM_TEXT_LEN to (280K - ROM_DATA0_LEN)
-	-- the lack of custom ISA instructions means we have to change the linker script, as the section overflows

4.	Run ./vendor/hisi/hi3861/hi3861/build.sh wifiiot
