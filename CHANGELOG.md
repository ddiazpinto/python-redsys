# 1.0.2

## Fixed

- Secret is now a mandatory parameter
- Required Python is now ^3.7
- Fix the license
- Code and messages improvements, thanks @jdelarubia
  
# 1.0.1

## Fixed

- Fix required Python version

# 1.0.0

## Added

- Use mypy to type codebase
- Request and Response tests
- Use @staticmethod where necessary

## Changed

- Requests are now initialized with a dictionary of parameters(example on README)
- The code and message of a Response can now be accessed from `response.code` and `response.message`
- is_paid, is_refunded, is_canceled and is_authorized are now properties instead of methods

## Fixed

- Correctly enforce abstract class

# 0.4.0

## Added

- Client tests

## Changed

- Replaced pycrypto(which is abandoned) by PyCryptodome
- Migrated all the constants to a single file(currencies, languages and transactions)
- Drop compatibility with Python 2.x
- Code cleanup

# 0.3.0

- Initial release
