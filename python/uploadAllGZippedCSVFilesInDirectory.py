import os
import requests

# Script for uploading all .csv.gz files in a hierarchical folder structure to the platform.
# change the user, password, dataKey, and folder for your case.
# Where user and password are API keys
# (to be set by navigating to the top right menu bar and clicking on the user icon and choosing 'User management')
# The dataKey is the key that can be found by going to your data set,
# click edit, and then go to Upload Data.
# At the bottom of this page you will see the data key.

# Note that this script assumes you already initialized a new data set, by providing a name, description, and defined
# the data properties (and optionally metadata properties). These actions can also be scripted, but this is not
# shown in this script. Please refer to https://docs.platform-xyzt.ai/tutorials/using-the-api/goal.html for using
# an api generator to get simple access to the full xyzt.ai platform REST API

url = "https://api.platform-xyzt.ai/public/api"
user = "put_here_your_api_user_name"
password = "put_here_your_api_user_password"
dataKey = "put_here_the_data_set_id"
folder = "/Users/bartadams/Data/onboarding/Onboarding/vessels/data"


def request_token():
    print("------------------------------------")
    print("Requesting token")

    payload = {
        "userName": user,
        "password": password
    }

    response = requests.post(f"{url}/tokens", json=payload)
    code = response.status_code

    print(code)

    if code == 200:
        body = response.json()
        jwtToken = body.get("jwtToken", "")
        print("Requesting token success")
        return jwtToken
    else:
        print(f"Could not request jwt token, probably your API user and password are wrong, got error code {code}")
        return None


def upload_file(jwt_token, file_path):
    print(f"Uploading file: {file_path}")

    files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), 'application/x-gzip')}
    headers = {'Authorization': f'Bearer {jwt_token}'}

    response = requests.post(f"{url}/datasets/{dataKey}/data/upload", files=files, headers=headers)
    code = response.status_code

    print(code)

    if code == 200:
        print("Uploading file success")
    else:
        print(f"Could not upload file, got error code {code}")


# Find all .csv.gz files in the current directory and its subdirectories
for root, dirs, files in os.walk(folder, topdown=False):
    for file in files:
        if file.endswith('.csv.gz'):
            file_path = os.path.join(root, file)

            # Request a token for each file upload
            jwt_token = request_token()

            if jwt_token is not None:
                upload_file(jwt_token, file_path)
