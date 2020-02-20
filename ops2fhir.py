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

# TODO: function to create medication and validate it against server.
def create_medication(col, meta_profile):
    pat_medication = medication.Medication()
    pat_medication.meta = meta_profile
    pat_medication.id = create_unique_id()
    # TODO: fill Medication object
    pat_med_ingredient = medication.MedicationIngredient()
    # TODO: fill MedicationIngredient object

    return pat_medication, pat_med_ingredient

# TODO: function to create MedicationStatement and validate it against server.
def create_medication_statement(col, meta_profile, medication_id, patient_id):
    medication_statement = medicationstatement.MedicationStatement()
    medication_statement.meta = meta_profile
    medication_statement.id = create_unique_id()
    medication_statement.status = 'completed'
    # reference to medication object
    # TODO: The corresponding Medication instance should already be on the server! Get ID from respective Medication object
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
    route_code_coding.code = col['Routes and Methods of Administration - Concept Code']
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

    ingredient_codes = []

    # ingredients
    if col['UNII_Substanz_allg'] is not None:
        system_unii = 'http://fdasis.nlm.nih.gov'
        code_unii = col['UNII_Substanz_allg']
        ingredient_code_unii = create_ingredient_code_x(system_unii, code_unii, ingredient_ext)
        ingredient_codes.append(ingredient_code_unii)

    if not(np.isnan(col['ASK_Substanz_allg'])):
        system_ask = 'http://fhir.de/CodeSystem/ask'
        code_ask = col['ASK_Substanz_allg']
        ingredient_code_ask = create_ingredient_code_x(system_ask, code_ask, ingredient_ext)
        ingredient_codes.append(ingredient_code_ask)


    if col['CAS_Substanz_allg'] is not None:
        system_cas = 'urn:oid:2.16.840.1.113883.6.61'
        code_cas = col['CAS_Substanz_allg']
        ingredient_code_cas = create_ingredient_code_x(system_cas, code_cas, ingredient_ext)
        ingredient_codes.append(ingredient_code_cas)

    med_ingredient.itemCodeableConcept = ingredient_codes

    return [med_ingredient]

def create_ingredient_code_x(system, code, ingredient_ext):
    ingredient_code = codeableconcept.CodeableConcept()
    ingredient_code_coding = coding.Coding()
    ingredient_code_coding.system = system
    ingredient_code_coding.code = code
    ingredient_code_coding.display = col['Substanz_allg_engl_INN_oder_sonst']
    ingredient_code_coding.extension = [ingredient_ext]
    ingredient_code.coding = [ingredient_code_coding]

    return ingredient_code

# TODO: function shall make sure that the created UUIDs are unique (not yet in the server)
def create_unique_id():
    new_uuid = uuid.uuid4()
    # TODO: get all IDs from server and compare to new ID

    return new_uuid

# TODO: function to start session with vonk client
def vonk_client(server_url, headers, charite_proxy, verification):
    vonk_session = requests.session(server_url)
    # TODO: Proxy parameter should be optional!!
    vonk_session.proxies = charite_proxy
    vonk_session.verify = verification

    return vonk_session

# TODO: connection to fhir_patient_generator to create patient-bundles?
'''
headers = {
    'Accept': 'application/fhir+json; fhirVersion=4.0',
    'Content-Type': 'application/fhir+json; fhirVersion=4.0'
}

# %%
medicationStatement = medicationstatement.MedicationStatement()
for index, row in ops_data.iterrows():
    # with open(f"{row[0]}.json", "w") as f:

    # das MII Profil in den Metadaten angeben
    msMeta = meta.Meta()
    msMeta.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/MedicationStatement']
    medicationStatement.meta = msMeta

    # sollte bei retrospektiver Betrachtung auf fix auf 'completed' stehen
    medicationStatement.status = 'completed'

    # medication[x]
    pat_medication = medication.Medication()

    medId = uuid.uuid4()
    pat_medication.id = str(medId)

    medMeta = meta.Meta()
    medMeta.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication']
    pat_medication.meta = medMeta

    medIngredient = medication.MedicationIngredient()

    # ingredientType
    ingredientExt = extension.Extension()
    ingredientExt.url = 'https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/wirkstofftyp'

    ingredientExtCoding = coding.Coding()
    ingredientExtCoding.system = 'http://www.nlm.nih.gov/research/umls/rxnorm'
    ingredientExtCoding.code = 'IN'
    ingredientExtCoding.display = 'ingredient'

    ingredientExt.valueCoding = ingredientExtCoding

    # ingredients
    if row[40] is not None:
        pass
    else:
        ingredientCode = codeableconcept.CodeableConcept()
        ingredientCodeCoding = coding.Coding()
        ingredientCodeCoding.system = 'http://fdasis.nlm.nih.gov'
        ingredientCodeCoding.code = f'{row[40]}'
        ingredientCodeCoding.display = f'{row[38]}'
        ingredientCodeCoding.extension = [ingredientExt]
        ingredientCode.coding = [ingredientCodeCoding]
        medIngredient.itemCodeableConcept = ingredientCode

    if np.isnan(row[41]):
        pass
    else:
        ingredientCode = codeableconcept.CodeableConcept()
        ingredientCodeCoding = coding.Coding()
        ingredientCodeCoding.system = 'http://fhir.de/CodeSystem/ask'
        ingredientCodeCoding.code = f'{row[41]}'
        ingredientCodeCoding.display = f'{row[38]}'
        ingredientCodeCoding.extension = [ingredientExt]
        ingredientCode.coding = [ingredientCodeCoding]
        medIngredient.itemCodeableConcept = ingredientCode

    if row[42] is not None:
        pass
    else:
        ingredientCode = codeableconcept.CodeableConcept()
        ingredientCodeCoding = coding.Coding()
        ingredientCodeCoding.system = 'urn:oid:2.16.840.1.113883.6.61'
        ingredientCodeCoding.code = f'{row[42]}'
        ingredientCodeCoding.display = f'{row[38]}'
        ingredientCodeCoding.extension = [ingredientExt]
        ingredientCode.coding = [ingredientCodeCoding]
        medIngredient.itemCodeableConcept = ingredientCode

    pat_medication.ingredient = [medIngredient]

    msMedRef = fhirreference.FHIRReference()
    msMedRef.reference = 'Medication/' + str(medId)
    medicationStatement.medicationReference = msMedRef

    fname = 'Medication-' + row[0]+ '.json'
    with open('./output/' + fname, 'w') as outfile:
        json.dump(pat_medication.as_json(), outfile, indent=4)
    print("Medication json written to file {fn}".format(fn=fname))

    #first validate against the profile on the server
    req = requests.post(f'{fhir_test_server}/Medication/$validate', headers = headers, data = json.dumps(pat_medication.as_json()))
    print(req.status_code)

    #if resource is valid
    if req.status_code == 200:
        req1 = requests.post(f'{fhir_test_server}/Medication', headers = headers, data = json.dumps(pat_medication.as_json()))
        print(req1.status_code)

    # subject
    patient = patient.Patient()

    patId = uuid.uuid4()
    patient.id = str(patId)

    msSubj = fhirreference.FHIRReference()
    msSubj.reference = 'Patient/' + str(patId)
    medicationStatement.subject = msSubj

    fname = 'Patient-' + f'{patId}' + '.json'
    with open('./output/' + fname, 'w') as outfile:
        json.dump(patient.as_json(), outfile, indent=4)
    print("Patient json written to file {fn}".format(fn=fname))

    #first validate against the profile on the server
    req = requests.post(f'{fhir_test_server}/Patient/$validate', headers = headers, data = json.dumps(patient.as_json()))
    print(req.status_code)

    #if resource is valid
    if req.status_code == 200:
        req1 = requests.post(f'{fhir_test_server}/Patient', headers = headers, data = json.dumps(patient.as_json()))
        print(req1.status_code)

    # context

    # effective[x]
    # dateTime



    # effective[x]
    # Period
    msPeriod = prd.Period()
    msPeriod.start = fd.FHIRDate("2020-02-03T12:00:00+01:00")
    msPeriod.end = fd.FHIRDate("2020-02-04T12:00:00+01:00")
    medicationStatement.effectivePeriod = msPeriod

    # Dosage
    msDosage = dosage.Dosage()

    # Dosage.text
    msDosage.text = f'{row[1]}'

    # Dosage.route
    msRouteCode = codeableconcept.CodeableConcept()
    msRouteCodeCoding = coding.Coding()
    msRouteCodeCoding.system = 'http://standardterms.edqm.eu'
    msRouteCodeCoding.code = f'{row[14]}'
    msRouteCodeCoding.display = f'{row[15]}'
    msRouteCode.coding = [msRouteCodeCoding]
    msDosage.route = msRouteCode

    # Dosage.site
    msSiteCode = cc.CodeableConcept()
    msSiteCodeCoding = co.Coding()
    msSiteCodeCoding.system = ''
    msSiteCodeCoding.code = ''
    msSiteCodeCoding.display = ''
    msSiteCode.coding = [msSiteCodeCoding]
    msDosage.site = msSiteCode

    # Dosage.method
    msMethodCode = cc.CodeableConcept()
    msMethodCodeCoding = co.Coding()
    msMethodCodeCoding.system = ''
    msMethodCodeCoding.code = ''
    msMethodCodeCoding.display = ''
    msMethodCode.coding = [msMethodCodeCoding]
    msDosage.method = msMethodCode

    # doseAndRate
    msDoseAndRate = dosage.DosageDoseAndRate()

    # if isinstance(row[16], float) == True:
    if pd.isnull(row[10]) == False:
        # doseRange
        msDoseRange = range.Range()

        # low
        msDoseRangeLow = quantity.Quantity()
        msDoseRangeLow.value = row[9]
        msDoseRangeLow.unit = f'{row[12]}'
        msDoseRangeLow.system = 'http://unitsofmeasure.org'
        msDoseRangeLow.code = f'{row[11]}'

        #high
        msDoseRangeHigh = quantity.Quantity()
        msDoseRangeHigh = quantity.Quantity()
        msDoseRangeHigh.value = row[10]
        msDoseRangeHigh.unit = f'{row[12]}'
        msDoseRangeHigh.system = 'http://unitsofmeasure.org'
        msDoseRangeHigh.code = f'{row[11]}'

        msDoseRange.low = msDoseRangeLow
        msDoseRange.high = msDoseRangeHigh
        msDoseAndRate.doseRange = msDoseRange
        msDosage.doseAndRate = [msDoseAndRate]

    else:
        # doseQuantity (SimpleQuantity)
        msDoseQuantity = quantity.Quantity()
        msDoseQuantity.value = row[9]
        msDoseQuantity.unit = f'{row[12]}'
        msDoseQuantity.system = 'http://unitsofmeasure.org'
        msDoseQuantity.code = f'{row[11]}'

        msDoseAndRate.doseQuantity = msDoseQuantity
        msDosage.doseAndRate = [msDoseAndRate]

    medicationStatement.dosage = [msDosage]

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
    ops_data['Einheit_Wert_min'] = ops_data['Einheit_Wert_min'].str.replace(',', '.').astype(float)
    ops_data['Einheit_Wert_max'] = ops_data['Einheit_Wert_max'].str.replace(',', '.').astype(float)

    for row, col in ops_data.iterrows():
        med_statement_dosage = create_dosage(col)
        medication_ingredient = create_ingredient(col)

    # Vonk server data
    # fhir_test_server = 'http://localhost:4080/'
    server_url = 'http://s-hdp-diz.charite.de:28181'
    headers = {
        'Accept': 'application/fhir+json; fhirVersion=4.0',
        'Content-Type': 'application/fhir+json; fhirVersion=4.0'
    }

    # create Medication
    meta_medication = meta.Meta()
    meta_medication.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication']
    pat_medication = create_medication(ops_data, server_url, meta_medication)

    # create MedicationStatement
    # MII MedicationStatement profile in meta
    meta_medication_statement = meta.Meta()
    meta_medication_statement.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/MedicationStatement']
    pat_medication_statement = create_medication_statement(ops_data, server_url, meta_medication_statement)



