class AccountError(Exception):
    pass


class AccountingEquationViolationError(AccountError):
    pass


class AccountTypeOnChildAccountError(AccountError):
    pass


class TransactionOnParentAcError(AccountError):
    pass
