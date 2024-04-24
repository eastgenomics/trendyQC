from typing import Any


class CustomTests:
    """ Class that will harbour custom tests to handle the horible things that
    can happen when ingesting MultiQC data
    """
    
    def assertKindaEqual(self, value1: Any, value2: Any):
        """ Assertion test to handle cases where a string was converted into a
        None and imported as such:
        {
            "125416805-23265R0011-23SNPID19-F_S60_L001_sorted": {
                "HS_LIBRARY_SIZE": ""
            }
        }

        In this case, None will be imported in the database since the model has
        a FloatField for this field and a blank value cannot be assigned.

        Args:
            value1 (Any): First value to assess
            value2 (Any): Second value to assess

        Raises:
            AssertionError: if the values are not equal, check if they are both
            either "" or None
        """

        if value1 != value2:
            if value1 not in ["", None] and value2 not in ["", None]:
                # happy stores data as strings, need conversion to be sure that
                # the value are really not equal
                try:
                    float(value1)
                    float(value2)
                except Exception:
                    raise AssertionError(
                        f"{value1} is not kinda equal to {value2}"
                    )
                else:
                    if float(value1) != float(value2):
                        raise AssertionError(
                            f"{value1} is not equal to {value2}"
                        )
            else:
                if value1 == "NA":
                    if value2 is not None:
                        raise AssertionError(
                            f"{value1} is not equal to {value2}"
                        )
