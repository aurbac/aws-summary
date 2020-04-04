## AWS Summary

Clone this github project and inside the folder execute the following commands.

1\. Install requirements.

``` bash
pip install -t lib -r requirements.txt
```

2\. Setting the environment variables with IAM credentials for your user (**with read only permissions**).

``` bash
export AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION=us-east-1
```

3\. Execute the script.

``` bash
python aws_summary.py
```

4\. You can find the results in **services** folder.