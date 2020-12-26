
[![PyPI version](https://badge.fury.io/py/python-redsys.svg)](https://badge.fury.io/py/python-redsys)

# Welcome to python-redsys!

A simple, clean and less dependant client to handle payments through the
Redsys platform using one of the available methods: _redirect connection_ or (secure method).

The purpose of this library is to provide a normalized interface between
Redsys and other Python applications.

**About RedirectClient**

Although _redirect connection_ depends on a webserver to resolve the
communication step, the RedirectClient provided in this library does not
assume any kind of procedure to resolve that step; it merely prepares
the necessary parameters to make a request and handles the corresponding
response parameters. That's what less dependant means.

## Example using _redirect connection_

### 0. Install python-redsys

You can add python-redsys to your project with pip:
> pip install python-redsys

Or with poetry:
> poetry add python-redsys

### 1. Instantiate the redirect client

```python
from decimal import Decimal as D, ROUND_HALF_UP
from redsys import transactions
from redsys.client import RedirectClient

secret_key = "123456789abcdef"
sandbox = False
client = RedirectClient(secret_key, sandbox)
```

### 2. Create a request

```python
request = client.create_request()
```

### 3. Set up the request parameters

```python
request.merchant_code = "100000001"
request.terminal = "1"
request.transaction_type = transactions.STANDARD_PAYMENT
request.currency = currencies.EUR
request.order = "000000001"
# The amount must be defined as decimal and pre-formatted with only two decimals
request.amount = D("10.56489").quantize(D(".01"), ROUND_HALF_UP)
request.merchant_data = "merchant data for tracking purpose like order_id, session_key, ..."
request.merchant_name = "Example Commerce"
request.titular = "Example Ltd."
request.product_description = "Products of Example Commerce"
request.merchant_url = "https://example.com/redsys/response"
```

### 4. Prepare the request

This method returns a dict with the necessary post parameters that are
needed during the communication step.

```python
args = client.prepare_request(request)
```

### 5. Communication step

Redirect the _user-agent_ to the corresponding RedSys's endpoint using
the post parameters given in the previous step.

After the payment process is finish, RedSys will respond making a
request to the `merchant_url` defined in step 3.

### 6. Create and check the response

Create the response object using the received parameters from Redsys.
The method `create_response()` throws a `ValueError` in case the
received signature is not equal to the calculated one using the
given `merchant_parameters`. This normally means that the response **is
not coming from Redsys** or that it **has been compromised**.

```python
signature = "YqFenHc2HpB273l8c995...."
merchant_parameters = "AndvIh66VZdkC5TG3nYL5j4XfCnFFbo3VkOu9TAeTs58fxddgc..."
signature_version = "HMAC_SHA256_V1"
response = client.create_response(signature, merchant_parameters, signature_version)
if response.is_paid():
    # Do the corresponding actions after a successful payment
else:
    # Do the corresponding actions after a failed payment
    raise Exception(response.response, response.message)
```

**Methods for checking the response:**

According to the RedSys documentation:

- `response.is_paid()`: Returns `True` if the response code is
  between 0 and 99 (both included).
- `response.is_canceled()`: Returns `True` if the response code
  is 400.
- `response.is_refunded()`: Returns `True` if the response code
  is 900.
- `response.is_authorized()`: Returns `True` if the response is
  **paid**, **refunded** or **canceled**.

Also, you can directly access the code or the message defined in Redsys
documentation using `response.response_code` or
`response.response_message`.

## Contributions

Please, feel free to send any contribution that maintains the _less
dependant_ philosophy.
