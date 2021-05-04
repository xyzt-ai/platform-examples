#/bin/bash

# Script for uploading all .csv.gz files in a hierarchical folder structure to the platform.
# change the user, password, and dataKey for your case. Where user and password are API keys (to be set by navigating to the top right menu bar and clicking on the user icon and choosing 'User management'
# The dataKey is the key that can be found by going to your data set, click edit, and then go to Upload Data. At the bottom of this page you will see the data key.

url="https://dev-api.platform-xyzt.ai/public/api"
user="api-user-f65a5e22-ddb7-47c9-96e8-a1a5171c1a86@xyzt.ai"
password="69023c3f-0962-4c33-80c7-ed9618e3a22e"
dataKey="09dcbae2-0504-4b38-88e6-a09592f39db1"

for f in $(find . -name '*.csv.gz'); do
	# We first authorize ourselves by requesting a jwt token. This token is requested before each file upload, as it might expire if a file upload takes a long time
	echo "------------------------------------"
	echo "Requesting token"
	response=$(curl -s -w "\n%{http_code}" -X POST "$url/tokens" -H  "accept: application/json" -H "Content-Type: application/json" -d "{\"userName\":\"$user\",\"password\":\"$password\"}")
	response=(${response[@]}) # convert to array
	code=${response[-1]} # get last element which is the http code
	echo $code
	if [ $code == 200 ] 
	then
		# Extract the token so that we can pass it to authorize the file upload
		body=${response[@]::${#response[@]}-1} # get all elements except last
		jwtToken=$(echo $body  | grep -Po '"jwtToken":"\K[^"]*') # extract token itself from the body
		echo "Requesting token success"
		
		# Uploading the file it
		echo "Uploading file: $f"
		response=$(curl -s -w "\n%{http_code}" -X POST "$url/datasets/$dataKey/data/upload" -H  "Accept: application/json" -H  "Content-Type: multipart/form-data" -H "Authorization: Bearer $jwtToken" -F "file=@$f;type=application/x-gzip")
		response=(${response[@]}) # convert to array
		code=${response[-1]} # get last element which is the http code
		echo $code
		if [ $code == 200 ]
		then
			echo "Uploading file success"
		else
			echo "Could not upload file, got error code $code"
		fi
	else
		echo "Could not request jwt token, probably your API user and password are wrong, got error code $code"
	fi
done
