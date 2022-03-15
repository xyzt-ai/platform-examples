# xyzt.ai API examples

This repository contains example scripts that use the public API of the xyzt.ai platform.

The scripts are grouped per language in separate directories.

To upload data to the xyzt.ai platform using the API, you first need to create an API user:
- Click on the account icon in the top right corner
- Select User Management
- Navigate to the bottom of the page and create an API user
- Take note of the API username and password

To upload using the API, you first need to create and configure a Data Set. You do so on the platform as follows:
- Click on Data sets from the navigation bar on the left
- Click on the ADD NEW DATA SET button
- Configure the data set, by uploading the data set properties csv file and setting the processing settings
- You can then upload data with the API

## Java examples

* The Java examples require JDK 11 or higher.
* Each script is a single file without any additional dependencies.
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

* The bash examples use curl.
* The parameters to modify are set in the first lines:
   - user: this is the API username
   - password: this is the API user's password
   - dataKey: this is the data set id

## Python library

* The Python library contains a single API class which uses urllib3 to communicate with the xyzt.ai platform API.
* API calls which return a status code < 200 or >= 300 will cause a `urllib3.exceptions.HTTPError` to be raised.
* Example code can be found in the documentation block at the top of the file.
