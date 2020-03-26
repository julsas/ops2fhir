from medicationgenerator import medication_generator
from patientgenerator import client
import json

def generate_and_post_medications(base_url, verification, coding_col_names, coding_display_col, extension_url,
                                  extension_system, extension_code, extension_display, meta_profile, ops_df):
    generator = medication_generator.MedicationGenerator(
        coding_col_names = coding_col_names,
        coding_display_col = coding_display_col,
        extension_url = extension_url,
        extension_system = extension_system,
        extension_code = extension_code,
        extension_display = extension_display,
        meta_profile = meta_profile,
        ops_df = ops_df
    )

    vonk_client = client.VonkClient(base_url, verification)
    resource_enum = client.ResourceEnum()
    med_ids = []

    for med in generator:
        fhir_med = med.to_fhir()
        response = vonk_client.post_resource(fhir_med, resource_enum.MEDICATION, True)

        if response.status_code != 200:
            raise Exception(f'Failed to validate medication: {response.content}')

        response = vonk_client.post_resource(fhir_med, resource_enum.MEDICATION, False)
        if response.status_code != 201:
            raise Exception(f'Failed to post medication: {response.content}')

        response_text = json.loads(response.text)
        med_id = response_text['id']
        print(f'Posted Medication: {med_id}')
        med_ids.append(med_id)

    return med_ids