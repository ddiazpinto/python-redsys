"""Credential-on-File (COF / MIT) indicators for stored-credential payments."""

# Ds_Merchant_Cof_Ini: is this the first stored-credential transaction?
INITIAL = 'S'
SUBSEQUENT = 'N'

# Ds_Merchant_Cof_Type: reason for the stored-credential transaction.
INSTALLMENT = 'I'
RECURRING = 'R'
REAUTHORIZATION = 'H'
RESUBMISSION = 'E'
DELAYED = 'D'
INCREMENTAL = 'M'
NO_SHOW = 'N'
UNSCHEDULED = 'C'

COF_TYPES = (
    INSTALLMENT,
    RECURRING,
    REAUTHORIZATION,
    RESUBMISSION,
    DELAYED,
    INCREMENTAL,
    NO_SHOW,
    UNSCHEDULED,
)

# Ds_Merchant_Identifier sentinel that asks RedSys to create and return a new card token.
REQUEST_TOKEN = 'REQUIRED'
