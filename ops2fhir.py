import json
import uuid
import math
import pandas as pd
import numpy as np
import requests
from fhirclient.models import (
    medicationstatement,
    medication,
    patient,
    dosage,
    timing,
    fhirreference,
    meta,
    fhirdate,
    period,
    codeableconcept,
    coding,
    quantity,
    ratio,
    range,
    humanname,
    extension
)

import patientgenerator

# TODO: function to create medication and validate it against server.
def create_medication(col, meta_profile):
    pat_medication = medication.Medication()
    pat_medication.meta = meta_profile
    #pat_medication.id = create_unique_id()
    # TODO: fill Medication object
    pat_med_ingredient = create_ingredient(col)
    pat_medication.ingredient = pat_med_ingredient

    return pat_medication

# TODO: function to create MedicationStatement and validate it against server.
def create_medication_statement(col, meta_profile, medication_id, patient_id):
    medication_statement = medicationstatement.MedicationStatement()
    medication_statement.meta = meta_profile
    #medication_statement.id = create_unique_id()
    medication_statement.status = 'completed'
    # reference to medication object
    reference_medication = fhirreference.FHIRReference()
    reference_medication.reference = 'Medication/' + str(medication_id)
    medication_statement.medicationReference = reference_medication
    # reference to patient
    # TODO: The corresponding Patient instance should already be on the server! Get ID from respective Patient object
    reference_patient = fhirreference.FHIRReference()
    reference_patient.reference = 'Patient/' + str(patient_id)
    medication_statement.subject = reference_patient
    # TODO: effectiveDateTime shouldn't be constant....
    medication_statement_dt = fhirdate.FHIRDate("2020-02-13T12:00:00+01:00")
    medication_statement.effectiveDateTime = medication_statement_dt

    medication_statement.dosage = create_dosage(col)

    return medication_statement

def create_dosage(col):
    # Dosage
    med_statement_dosage = dosage.Dosage()

    # Dosage.text
    med_statement_dosage.text = col['opsText']

    # Dosage.route
    route_code = codeableconcept.CodeableConcept()
    route_code_coding = coding.Coding()
    route_code_coding.system = 'http://standardterms.edqm.eu'
    route_code_coding.code = str(col['Routes and Methods of Administration - Concept Code'])
    route_code_coding.display = col['Routes and Methods of Administration - Term']
    route_code.coding = [route_code_coding]
    med_statement_dosage.route = route_code

    # doseAndRate
    dose_and_rate = dosage.DosageDoseAndRate()

    # if isinstance(row[16], float) == True:
    if not(pd.isnull(col['Einheit_Wert_max'])):
        # doseRange
        dose_range = range.Range()

        # low
        dose_range_low = quantity.Quantity()
        dose_range_low.value = col['Einheit_Wert_min']
        dose_range_low.unit = col['UCUM-Description']
        dose_range_low.system = 'http://unitsofmeasure.org'
        dose_range_low.code = col['UCUM-Code']

        # high
        dose_range_high = quantity.Quantity()
        dose_range_high.value = col['Einheit_Wert_max']
        dose_range_high.unit = col['UCUM-Description']
        dose_range_high.system = 'http://unitsofmeasure.org'
        dose_range_high.code = col['UCUM-Code']

        dose_range.low = dose_range_low
        dose_range.high = dose_range_high
        dose_and_rate.doseRange = dose_range
        med_statement_dosage.doseAndRate = [dose_and_rate]

    else:
        # doseQuantity (SimpleQuantity)
        dose_quantity = quantity.Quantity()
        dose_quantity.value = col['Einheit_Wert_min']
        dose_quantity.unit = col['UCUM-Description']
        dose_quantity.system = 'http://unitsofmeasure.org'
        dose_quantity.code = col['UCUM-Code']

        dose_and_rate.doseQuantity = dose_quantity
        med_statement_dosage.doseAndRate = [dose_and_rate]

    return [med_statement_dosage]

def create_ingredient(col):
    med_ingredient = medication.MedicationIngredient()

    # ingredientType
    ingredient_ext = extension.Extension()
    ingredient_ext.url = 'https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/wirkstofftyp'

    ingredient_ext_coding = coding.Coding()
    ingredient_ext_coding.system = 'http://www.nlm.nih.gov/research/umls/rxnorm'
    ingredient_ext_coding.code = 'IN'
    ingredient_ext_coding.display = 'ingredient'

    ingredient_ext.valueCoding = ingredient_ext_coding

    ingredient_code = codeableconcept.CodeableConcept()
    ingredient_codings = []

    # ingredients
    if col['UNII_Substanz_allg'] is not None:
        system_unii = 'http://fdasis.nlm.nih.gov'
        code_unii = col['UNII_Substanz_allg']
        ingredient_code_unii = create_ingredient_code_x(system_unii, code_unii, ingredient_ext)
        ingredient_codings.append(ingredient_code_unii)

    if not(np.isnan(col['ASK_Substanz_allg'])):
        system_ask = 'http://fhir.de/CodeSystem/ask'
        code_ask = str(col['ASK_Substanz_allg'])
        ingredient_code_ask = create_ingredient_code_x(system_ask, code_ask, ingredient_ext)
        ingredient_codings.append(ingredient_code_ask)


    if col['CAS_Substanz_allg'] is not None:
        system_cas = 'urn:oid:2.16.840.1.113883.6.61'
        code_cas = col['CAS_Substanz_allg']
        ingredient_code_cas = create_ingredient_code_x(system_cas, code_cas, ingredient_ext)
        ingredient_codings.append(ingredient_code_cas)

    ingredient_code.coding = ingredient_codings
    med_ingredient.itemCodeableConcept = ingredient_code


    return [med_ingredient]

# Helper function for create_ingredient_code_x()
def create_ingredient_code_x(system, code, ingredient_ext):
    ingredient_code_coding = coding.Coding()
    ingredient_code_coding.system = system
    ingredient_code_coding.code = code
    ingredient_code_coding.display = col['Substanz_allg_engl_INN_oder_sonst']
    ingredient_code_coding.extension = [ingredient_ext]

    return ingredient_code_coding

# function no longer needed. Objects shall take ID given by the server...
def create_unique_id():
    new_uuid = str(uuid.uuid4())
    # TODO: get all IDs from server and compare to new ID

    return new_uuid

# TODO: function to start session with vonk client
def vonk_client(headers, verification):
    vonk_session = requests.session()
    # TODO: Proxy parameter should be optional!!
    vonk_session.verify = verification
    vonk_session.headers = headers

    return vonk_session

'''
for index, row in ops_data.iterrows():
    # with open(f"{row[0]}.json", "w") as f:

    # sollte bei retrospektiver Betrachtung auf fix auf 'completed' stehen
    medicationStatement.status = 'completed'

    #first validate against the profile on the server
    req = requests.post(f'{fhir_test_server}/Medication/$validate', headers = headers, data = json.dumps(pat_medication.as_json()))
    print(req.status_code)

    #if resource is valid
    if req.status_code == 200:
        req1 = requests.post(f'{fhir_test_server}/Medication', headers = headers, data = json.dumps(pat_medication.as_json()))
        print(req1.status_code)

    #first validate against the profile on the server
    req = requests.post(f'{fhir_test_server}/Patient/$validate', headers = headers, data = json.dumps(patient.as_json()))
    print(req.status_code)

    #if resource is valid
    if req.status_code == 200:
        req1 = requests.post(f'{fhir_test_server}/Patient', headers = headers, data = json.dumps(patient.as_json()))
        print(req1.status_code)

    # effective[x]
    # Period
    #msPeriod = prd.Period()
    #msPeriod.start = fd.FHIRDate("2020-02-03T12:00:00+01:00")
    #msPeriod.end = fd.FHIRDate("2020-02-04T12:00:00+01:00")
    #medicationStatement.effectivePeriod = msPeriod

    fname = 'MedicationStatement' + f'{row[0]}' + '.json'
    with open('./output/' + fname, 'w') as outfile:
        json.dump(medicationStatement.as_json(), outfile, indent=4)
    print("MedicationStatement json written to file {fn}".format(fn=fname))

    #first validate against the profile on the server
    req = requests.post(f'{fhir_test_server}/MedicationStatement/$validate', headers = headers, data = json.dumps(medicationStatement.as_json()))
    print(req.status_code)

    #if resource is valid
    if req.status_code == 200:
        req1 = requests.post(f'{fhir_test_server}/MedicationStatement', headers = headers, data = json.dumps(medicationStatement.as_json()))
        print(req1.status_code)
'''
if __name__ == '__main__':
    ops_data = pd.read_csv('./ops_subs_merged_edit_test_neu.csv', encoding='ISO-8859-1')
    # fix csv values to avoid confusion with delimiter ','
    ops_data['Einheit_Wert_min'] = ops_data['Einheit_Wert_min'].str.replace(',', '.').astype(float)
    ops_data['Einheit_Wert_max'] = ops_data['Einheit_Wert_max'].str.replace(',', '.').astype(float)

    # Vonk server data
    # fhir_test_server = 'http://localhost:4080/'
    server_url = 'http://s-hdp-diz.charite.de:28182'
    headers = {
        'Accept': 'application/fhir+json; fhirVersion=4.0',
        'Content-Type': 'application/fhir+json; fhirVersion=4.0'
    }

    vonk_session = vonk_client(headers, False)

    # Define profiles
    meta_medication = meta.Meta()
    meta_medication.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication']
    meta_medication_statement = meta.Meta()
    meta_medication_statement.profile = [
        'https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/MedicationStatement']

    for row, col in ops_data.iterrows():
        #med_statement_dosage = create_dosage(col)
        #medication_ingredient = create_ingredient(col)
        pat_medication = create_medication(col, meta_medication)
        # validate against profile
        validate_medication = vonk_session.post(f'{server_url}/Medication/$validate', data=json.dumps(pat_medication.as_json()))
        # if valid with profile, post to server
        if validate_medication.status_code != 200:
            raise Exception(f'Failed to validate Medication resource: {validate_medication.text}')

        post_medication = vonk_session.post(f'{server_url}/Medication/', data=json.dumps(pat_medication.as_json()))

        if post_medication.status_code != 201:
            raise Exception('Failed to create Medication')

        posted_medication = json.loads(post_medication.text)
        med_id = posted_medication['id']
        print(f'Posted Medication: {med_id}')

        post_patient = patientgenerator.generate_and_post_patients(
            base_url=server_url,
            profile_url='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Patient',
            num_pat=1,
            first_names_path='../fhir_patient_generator/input/first_names.json',
            last_names_path='../fhir_patient_generator/input/last_names.json',
            genders_path='../fhir_patient_generator/input/genders.json',
            postal_codes_path='../fhir_patient_generator/input/zuordnung_plz_ort_landkreis.csv',
            name_use='official',
            ident_system='http://fhir.de/NamingSystem/gkv/kvid-10'
        )
        posted_patient = json.loads(post_patient.text)
        pat_id = posted_patient['id']

        pat_med_statement = create_medication_statement(col, meta_medication_statement, med_id, pat_id)
        validate_med_statement = vonk_session.post(f'{server_url}/MedicationStatement/$validate',
                                                   data=json.dumps(pat_med_statement.as_json()))

        if validate_med_statement.status_code != 200:
            raise Exception('Failed to validate MedicationStatement!')

        post_med_statement = vonk_session.post(f'{server_url}/MedicationStatement',
                                                   data=json.dumps(pat_med_statement.as_json()))

        if post_med_statement.status_code != 201:
            raise Exception('Failed to create MedicationStatement!')

        posted_med_statement = json.loads(post_med_statement.text)
        med_statement_id = posted_med_statement['id']
        print(f'Posted MedicationStatement: {med_statement_id}')