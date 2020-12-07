Hi3861 Huawei WiFi Iot SDK
---------------------------


First you need to create a login at hihope.org/login, the page is in Chinese.

![login1](https://github.com/riscv/riscv-code-size-reduction/blob/master/benchmarks/Hi3861_WiFi_IoT/pic1.jpg)

Click on the two yellow characters to get to the signup page

![login2](https://github.com/riscv/riscv-code-size-reduction/blob/master/benchmarks/Hi3861_WiFi_IoT/pic2.jpg)

Create a login and click on register, and then login on the previous page.


And when that’s worked you can go to the download page
 
http://www.hihope.org/download/AllDocuments
 
![download1](https://github.com/riscv/riscv-code-size-reduction/blob/master/benchmarks/Hi3861_WiFi_IoT/pic3.png)

Click on HI3861V100

![download2](https://github.com/riscv/riscv-code-size-reduction/blob/master/benchmarks/Hi3861_WiFi_IoT/pic4.png)

The download includes HCC which has the Huawei custom instructions included, e.g. 48-bit L.LI so you can try them out (using –femit-lli)
Download the release with the highest SPC number to get the latest version.
 
This link shows the custom instructions that we use:

https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/README.md
 
Note that the current build scripts use –fldm-stm-optimize and –msave-restore. These arguments should be ideally be removed and replaced with –mpush-pop.
The output elf is here:

Hi3861/SDK/HiHope_WiFi-IoT_Hi3861SPC021/output/bin/Hi3861_demo.out

