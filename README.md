# Requirements
Installing the requirements is done in two steps. First run
```
pip install -r requirements.txt
```
and then run
```
pip install --upgrade pyswisseph
```
The second command will have an error that `flatlib` requires `pyswisseph` version 2.8, however the Human Design section of this program requires version 2.10.
It will not cause any known issues to use `flatlib` with `pyswisseph` version 2.10.
