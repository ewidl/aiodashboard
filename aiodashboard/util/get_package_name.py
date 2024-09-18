_PACKAGE_NAME : str = __name__.split('.')[0]

def get_package_name() -> str:
    """
    Return the name of this package.
    """
    return _PACKAGE_NAME
