# Development Information

## Configure Development Environment

* Create a new Python Virtual Environment for qct_parse
    * Unix based (Mac or Linux):    
      `python3 -m venv name_of_env`
    * Windows:    
      `py -m venv name_of_env`
      (where 'name_of_env' is replaced with the name of your virtual environment)
* Activate virtual env
    * Unix based (Mac or Linux):     
      `source ./name_of_env/bin/activate`
    * Windows:     
      `name_of_env\scripts\activate`
* Install Package as editable package
    * Navigate to the repo root directory `path/to/qct-parse/`
    * Run the command:    
      `python -m pip install -e .`

## Run Tests

If you intend to develop the code for your proposes or contribute to the open source project, a test directory is provided in the repo.
* Activate virtual env (see Configure Development Environment)
* Install pytest
  `pip install pytest`
* Run tests
  `python -m pytest`

