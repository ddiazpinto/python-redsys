=========================
Welcome to python-redsys!
=========================

A simple, clean and less dependant client to handle payments through RedSys platform
(previously known as Sermepa) using the two types of connection defined by the platform:
*direct connection* (or webservice) and *redirect connection* or (secure method).

The purpose of this library is to provide a normalized interface between RedSys and other applications.

**About `RedirectClient`**

Although *redirect connection* depends on a webserver to resolve the communication step,
the `RedirectClient` provided in this library does not assume any kind of procedure to resolve that
step; it simply prepares the necessary parameters to make a request and handle the corresponding response parameters.
That's what less dependant means.

If you intend to use this library with django, take a look at <https://github.com/ddiazpinto/django-redsys>.
Django-redsys uses this library and extends it to resolve all the communication step. Unfortunately, it is not
documented at all but if you need some help, let me know submitting an issue.

Example using *redirect connection*
===================================

1. Instantiate the redirect client
----------------------------------
.. code-block:: python

    from decimal import Decimal as D, ROUND_HALF_UP
    from redsys import currencies, languages, parameters, transactions
    from redsys.client import RedirectClient

    secret_key = u'123456789abcdef'
    sandbox = False
    client = RedirectClient(secret_key, sandbox)


2. Create a request
-------------------
.. code-block:: python

    request = client.create_request()

3. Set up the request parameters
--------------------------------
.. code-block:: python

    request.merchant_code = u'100000001'
    request.terminal = u'1'
    request.transaction_type = transactions.STANDARD_PAYMENT
    request.currency = currencies.EUR
    request.order = u'000000001'
    # The amount must be defined as decimal and pre-formated with only two decimals
    request.amount = D('10.56489').quantize(D('.01'), ROUND_HALF_UP)
    request.merchant_data = 'merchant data for tracking purpose like order_id, session_key, ...'
    request.merchant_name = "Example Commerce"
    request.titular = "Example Ltd."
    request.product_description = "Products of Example Commerce"
    request.merchant_url = "https://example.com/redsys/response"

4. Prepare the request
----------------------
This method returns a dict with the necessary post parameters needed during the communication step.

.. code-block:: python

    args = client.prepare_request(request)

5. Communication step
---------------------
Redirect the *user-agent* to the corresponding RedSys's endpoint using the post parameters given in the previous step.

After the payment process is finish, RedSys will respond making a request to the `merchant_url` defined in the step 3.

6. Create and check the response
--------------------------------
Create the response object using the received parameters from RedSys. The method `create_response()`
throws a ``ValueError`` in case the received `signature` is not equal to the one calculated using
the given merchant_parameters. This normally means that the response **is not comming from RedSys** or that
**has been compromised**.

.. code-block:: python

    signature = "YqFenHc2HpB273l8c995...."
    merchant_parameters = "AndvIh66VZdkC5TG3nYL5j4XfCnFFbo3VkOu9TAeTs58fxddgc..."
    signature_version = "HMAC_SHA256_V1"
    response = client.create_response(signature, merchant_parameters, signature_version)
    if response.is_paid():
        # Do the corresponding actions after a successful payment
    else:
        # Do the corresponding actions after a failed payment
        raise Exception(response.response, response.message)

**Methods for checking the response:**

According to the RedSys documentation:
 - `response.is_paid()`: Returns ``True`` if the response code is between 0 and 99 (both included).
 - `response.is_canceled()`: Returns ``True`` if the response code is 400.
 - `response.is_refunded()`: Returns ``True`` if the response code is 900.
 - `response.is_authorized()`: Returns ``True`` if the response is **paid**, **refunded** or **canceled**.

Also, you can directly access the code or the message defined in RedSys documentation using `response.response_code`
or `response.response_message`.

Example using *direct connection* or *webservice*
=================================================
This connection method is not implemented yet.

Contributions
=============
Please, feel free to send any contribution that maintains the *less dependant* philosophy.
