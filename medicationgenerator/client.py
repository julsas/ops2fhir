import json
import requests
from fhirclient.models import patient
from enum import Enum

class ResourceEnum(Enum):
    PATIENT = 'Patient'
    MEDICATION = 'Medication'
    MEDSTATEMENT = 'MedicationStatement'
    PROCEDURE = 'Procedure'

class FhirClient:
    def __init__(self, base_url, verification=False, accept_fhir_format='json', send_fhir_format='json', fhir_version='4.0'):
        self.base_url = base_url

        headers = {
            'Accept': f'application/fhir+{accept_fhir_format}; fhirVersion={fhir_version}',
            'Content-Type': f'application/fhir+{send_fhir_format}; fhirVersion={fhir_version}'
        }
        self.session = requests.session()
        self.session.verify = verification
        self.session.headers = headers

    def post_resource(self, resource, resource_name:ResourceEnum, validate_flag:bool):
        url = f'{self.base_url}/{resource_name.value}'
        data = json.dumps(resource.as_json())
        if validate_flag:
            validate_url = f'{url}/$validate'
            response_valid = self.session.post(validate_url, data)

            # check connection
            if response_valid.status_code != 200:
                raise Exception(f'Connection to {validate_url} failed!')

            response_text = json.loads(response_valid.text)
            for issue in response_text['issue']:
                if issue['severity'] == 'error':
                    response_error = json.dumps(response_text['issue'], indent=4, sort_keys=True)
                    raise Exception(f'Resource not valid:\n {response_error}')

        # post resource
        response = self.session.post(url, data)
        if response.status_code != 201:
            raise Exception(f'Resource could not be created:\n {json.dumps(response.text, indent=4, sort_keys=True)}')

        return response

    def post_patient(self, pat:patient.Patient):
        url = f'{self.base_url}/Patient'
        data = json.dumps(pat.as_json())
        return self.session.post(url, data)

    def post_patient_validate(self, pat:patient.Patient):
        url = f'{self.base_url}/Patient/$validate'
        data = json.dumps(pat.as_json())
        return self.session.post(url, data)