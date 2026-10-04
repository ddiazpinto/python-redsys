
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
from redsys.constants import EUR, STANDARD_PAYMENT
from redsys.client import RedirectClient

secret_key = "123456789abcdef"
client = RedirectClient(secret_key)
```

### 2. Set up the request parameters

```python
parameters = {
  "merchant_code": "100000001",
  "terminal": "1",
  "transaction_type": STANDARD_PAYMENT,
  "currency": EUR,
  "order": "000000001",
  "amount": D("10.56489").quantize(D(".01"), ROUND_HALF_UP),
  "merchant_data": "test merchant data",
  "merchant_name": "Example Commerce",
  "titular": "Example Ltd.",
  "product_description": "Products of Example Commerce",
  "merchant_url": "https://example.com/redsys/response",
}
```

### 3. Prepare the request

This method returns a dict with the necessary post parameters that are
needed during the communication step.

```python
args = client.prepare_request(parameters)
```

### 4. Communication step

Redirect the _user-agent_ to the corresponding Redsys' endpoint using
the post parameters given in the previous step.

After the payment process is finished, Redsys will respond making a
request to the `merchant_url` defined in step 2.

### 5. Create and check the response

Create the response object using the received parameters from Redsys.
The method `create_response()` throws a `ValueError` in case the
received signature is not equal to the calculated one using the
given `merchant_parameters`. This normally means that the response **is
not coming from Redsys** or that it **has been compromised**.

```python
signature = "YqFenHc2HpB273l8c995...."
merchant_parameters = "AndvIh66VZdkC5TG3nYL5j4XfCnFFbo3VkOu9TAeTs58fxddgc..."
response = client.create_response(signature, merchant_parameters)
if response.is_paid:
    # Do the corresponding actions after a successful payment
else:
    # Do the corresponding actions after a failed payment
    raise Exception(response.code, response.message)
```

**Methods for checking the response:**

According to the Redsys documentation:

- `response.is_paid`: Returns `True` if the response code is
  between 0 and 99 (both included).
- `response.is_canceled`: Returns `True` if the response code
  is 400.
- `response.is_refunded`: Returns `True` if the response code
  is 900.
- `response.is_authorized`: Returns `True` if the response is
  **paid**, **refunded** or **canceled**.

Also, you can directly access the code or the message defined in Redsys
documentation using `response.code` or `response.message`.

## Contributions

Please, feel free to send any contribution that maintains the _less
dependant_ philosophy.
