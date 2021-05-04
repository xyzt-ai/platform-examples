# xyzt.ai API examples

This repository contains example scripts that use the public API of the xyzt.ai platform.

The scripts are grouped per language in separate directories.

## Java examples

* The Java examples require JDK 11 or higher.
* Each script is a single file without any additional dependencies
* Use `javac` to compile a single script. 
  For example to compile the `UploadAllFilesInDirectory.java` script, you would run:
  ```bash
  # Run this in the directory containing the UploadAllFilesInDirectory.java file
  javac UploadAllFilesInDirectory.java 
  ```
* Once you've compiled the script, you can run it with
  ```bash
  java UploadAllFilesInDirectory <required arguments>
  ```
  
## Bash examples

* The bash examples use curl
* The parameters to modify are set in the first lines (user, password, dataKey)
