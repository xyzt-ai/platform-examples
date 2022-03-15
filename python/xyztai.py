"""Tools for working with the xyzt.ai platform API

Uses urllib3 to communicate with the xyzt.ai API.

Example
-------

import xyztai
import urllib3
from pathlib import Path

xyztapi = xyztai.API(
    'apiuser-uuid@company.com',
    'api-password',
    'dataset-id'
    )

# Get and list datasets
datasets = xyztapi.retrieve_datasets()
for d in datasets:
    print('ID\t\t\t: {}'.format(d['id']))
    print('Name\t\t: {}'.format(d['name']))
    print('Description\t: {}'.format(d['description']))
    print('Batches[]\t: {}'.format(d['batches']), end='\n\n')

# Upload records, handling and reporting any upload error
try:
    datafile = Path('mydata.csv.gz')
    print(f'Uploading records from {datafile} ...', end=' ')
    xyztai.upload_records(datafile)
    print('OK')
except urllib3.exceptions.HTTPError as e:
    print(f'ERROR\n - {e}')

# Switch to a new dataset
xyztapi.did = 'new-dataset-id'
# ... API commands now target the new data set

License
-------

Copyrite (c) 2022, David McIver, Dedicated Systems Australia

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
“Software”), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib3
import json
from pathlib import Path
from typing import Dict, List

_apiroot : str = 'https://api.platform-xyzt.ai/public/api'
"""The root URL for calls to the xyzt.ai API
"""

class API:
    """Interface to the xyzt.ai platform API
    """
    
    def __init__(self, uname : str, password : str, dataset_id : str):
        """Initialise a new intance of the API class

        Parameters
        ----------
        uname : str
            The email address of the API user
        password : str
            The password of the API user
        dataset_id : str
            The ID of the dataset to upload the data to
        """
        self.uname = uname
        self.passwd = password
        self.did = dataset_id
        self._http = urllib3.PoolManager()
        self._encoding = 'utf-8'
    
    def _get_post_headers(self) -> Dict[str,str]:
        """Returns the headers which will be sent to the API with POST
        request

        Gets a fresh Authorization token from the API using the username
        and password and combines this with an Accept header. No
        Content-Type header is added because POST requests often add
        their own.
        
        Returns
        -------
        Dict[str,str]
            A dictionary containing headers for POST calls to the
            xyzt.ai API
        """
        url = _apiroot + '/tokens'
        data = { 'userName': self.uname, 'password': self.passwd }
        r = self._http.request('POST', url,
            headers={ 'Accept': 'application/json', 'Content-Type': 'application/json' },
            body=bytes(json.dumps(data), encoding=self._encoding)
            )
        if r.status < 200 or r.status >= 300:
            errmsg = json.loads(r.data.decode(self._encoding))['message']
            message = f'Request for auth token failed with status {r.status}: {errmsg}'
            raise urllib3.exceptions.HTTPError(message)
        token = json.loads(r.data.decode(self._encoding))['jwtToken']
        return {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            }

    def _get_content_type(self, file : Path) -> str:
        """Get the content type string for use in the POST request
        """
        rv : str = None
        if file.suffix == '.csv':
            rv = 'text/csv'
        elif file.suffix == '.gz':
            rv = 'application/x-gzip'
        if rv == None:
            raise ValueError('Unsupported file type')
        return rv

    def _upload(self, datatype : str, file : Path, batch : str):
        with file.open(mode='rb') as f:
            filedata = f.read()
        headers = self._get_post_headers()
        url = _apiroot + f'/datasets/{self.did}/{datatype}/upload'
        if batch:
            url = url + '?batch=' + batch.replace(' ', '_')
        r = self._http.request('POST', url, headers=headers, fields= {
            "file": (file.name, filedata, self._get_content_type(file))
            })
        # ... The above POST request will add its own Content-Type header
        if r.status < 200 or r.status >= 300:
            errmsg = json.loads(r.data.decode(self._encoding))['message']
            message = f'Upload of {datatype} file failed with status {r.status}: {errmsg}'
            raise urllib3.exceptions.HTTPError(message)

    def upload_records(self, file : Path, batch : str = None):
        """Upload records to a dataset, with the option of adding to a
        batch

        Parameters
        ----------
        file : Path
            Path of the CSV file containing the records to be uploaded
        batch : str
            The batch the records should be added to. Any spaces will
            be replaced with underscores.

        Raises
        ------
        HTTPError
            If the return status of the http request is an error. 
        ValueError
            If the file type is not a CSV or compressed CSV.
        """
        self._upload('data', file, batch)

    def upload_metadata(self, file : Path, batch : str = None):
        """Upload metadata to a dataset, with the option of adding to a
        batch

        Parameters
        ----------
        file : Path
            Path of the CSV file containing the metadata to be uploaded
        batch : str
            The batch the metadata should be added to. Any spaces will
            be replaced with underscores.

        Raises
        ------
        HTTPError
            If the return status of the http request is an error. 
        ValueError
            If the file type is not a CSV or compressed CSV.
        """
        self._upload('metadata', file, batch)
        
    def delete_batch(self, batch : str):
        """Schedule deletion of a batch of data from the dataset

        Parameters
        ----------
        batch : str
            The batch to be deleted. Any spaces will be replaced with
            underscores.

        Raises
        ------
        HTTPError
            If the return status of the http request is an error. 
        """
        if not batch:
            raise ValueError('batch cannot be null')
        url = _apiroot + f'/datasets/{self.did}/batches/' + batch.replace(' ', '_')
        headers = self._get_post_headers()
        r = self._http.request('DELETE', url, headers=headers)
        if r.status < 200 or r.status >= 300:
            errmsg = json.loads(r.data.decode(self._encoding))['message']
            message = f'Deletion of batch "{batch}" file failed with status {r.status}: {errmsg}'
            raise urllib3.exceptions.HTTPError(message)

    def retrieve_datasets(self) -> List[object]:
        """Retrieve a list of the available data sets

        Returns
        -------
        List[object] 
            List of data sets extracted from the json. Each data set is
            in the form of a dict object.
        """
        url = _apiroot + '/datasets'
        headers = self._get_post_headers()
        r = self._http.request('GET', url, headers=headers)
        if r.status < 200 or r.status >= 300:
            errmsg = json.loads(r.data.decode(self._encoding))['message']
            message = f'Retrieval of data sets Deletion of batch "{batch}" file failed with status {r.status}: {errmsg}'
            raise urllib3.exceptions.HTTPError(message)
        return json.loads(r.data.decode(self._encoding))