# Aws-account-integration

This project contains source code and supporting files for AWS Account integration automation

- pandrel_engine - Code for the application's Lambda function.
- tests - Unit tests for the application code.
- template.yaml - A template that defines the application's AWS resources.


## Notes
A account that need to be migrated should have MasterRole with all permission required to run AccountAnalyser. 
MasterRole Role should have trust policy for account from where you are triggering AccountAnalyser.


## Unit tests
Tests are defined in the `tests` folder in this project. Use PIP to install the [pytest](https://docs.pytest.org/en/latest/) and run unit tests.

```bash
aws-account-integration$ pip install pytest pytest-mock --user
aws-account-integration$ python -m pytest tests/ -v
```

#### Build and deployment bash script
- build.sh - Build, package and deploy the application on AWS.

