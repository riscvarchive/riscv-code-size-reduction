Hi3861 Huawei WiFi Iot SDK
---------------------------


First you need to create a login at hihope.org/login, the page is in Chinese.

<pic>

Click on the two yellow characters to get to the signup page

<pic>

Create a login and click on register, and then login on the previous page.


And when that’s worked you can go to the download page
 
http://www.hihope.org/download/AllDocuments
 
<pic>

Click on HI3861V100

<pic>


HCC has the Huawei custom instructions included, e.g. 48-bit L.LI so you can try them out (using –femit-lli)
Download the release with the highest SPC number to get the latest version.
 
This link shows the custom instructions that we use:

https://github.com/riscv/riscv-code-size-reduction/blob/master/existing_extensions/Huawei%20Custom%20Extension/README.md
 
Note that the current build scripts use –fldm-stm-optimize and –msave-restore. These arguments should be removed and replaced with –mpush-pop.
The output elf is here:

Hi3861/SDK/HiHope_WiFi-IoT_Hi3861SPC021/output/bin/Hi3861_demo.out
