class JournalError(Exception):
    pass


class TransactionUnbalancedError(JournalError):
    pass


class ZeroAmountError(JournalError):
    pass


class HasChildAccountError(JournalError):
    pass
