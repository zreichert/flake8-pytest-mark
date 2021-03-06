Error / Violation Codes
=======================

flak8-pytest-mark is a flake8 plugin that validates the presence of given pytest marks on test definitions.  All error codes generated by this plugin begin with M.  Here are all possible codes:


+---------------------------------------------------------------------------------------------------------+
| Code | Example Message                                                                                  |
+======+==================================================================================================+
| M401 + no configuration found ... please provide configured marks in a flake8 config                    |
+------+--------------------------------------------------------------------------------------------------+
| M5XX | test definition not marked with test_id                                                          |
+------+--------------------------------------------------------------------------------------------------+
| M6XX | does not match the configuration specified by pytest_mark1, badly formed hexadecimal UUID string |
+------+--------------------------------------------------------------------------------------------------+

The codes referenced in the table above that end in XX are configurable.  Up to 50 instances may be created.