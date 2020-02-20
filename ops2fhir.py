import json
import uuid
import math
import pandas as pd
import numpy as np
from requests import get, post, put
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

# TODO:
def create_medication(ops_data):


ops_data = pd.read_csv('./ops_subs_merged_edit_test_neu.csv', encoding = 'ISO-8859-1')
ops_data['Einheit_Wert_min'] = ops_data['Einheit_Wert_min'].str.replace(',', '.').astype(float)
ops_data['Einheit_Wert_max'] = ops_data['Einheit_Wert_max'].str.replace(',', '.').astype(float)
ops_data.head()

# %%
#define the server to post to 
# fhir_test_server = 'http://localhost:4080/'
fhir_test_server = 'http://s-hdp-diz.charite.de:28181'

headers = {
    'Accept':'application/fhir+json; fhirVersion=4.0',
    'Content-Type':'application/fhir+json; fhirVersion=4.0'
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
        medication = medication.Medication()

        medId = uuid.uuid4()
        medication.id = str(medId)

        medMeta = meta.Meta()
        medMeta.profile = ['https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication']
        medication.meta = medMeta

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

        medication.ingredient = [medIngredient]

        msMedRef = fhirreference.FHIRReference()
        msMedRef.reference = 'Medication/' + str(medId)
        medicationStatement.medicationReference = msMedRef

        fname = 'Medication-' + row[0]+ '.json'
        with open('./output/' + fname, 'w') as outfile:
            json.dump(medication.as_json(), outfile, indent=4)
        print("Medication json written to file {fn}".format(fn=fname))

        #first validate against the profile on the server
        req = post(f'{fhir_test_server}/Medication/$validate', headers = headers, data = json.dumps(medication.as_json()))
        print(req.status_code)

        #if resource is valid
        if req.status_code == 200:
            req1 = post(f'{fhir_test_server}/Medication', headers = headers, data = json.dumps(medication.as_json()))
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
        req = post(f'{fhir_test_server}/Patient/$validate', headers = headers, data = json.dumps(patient.as_json()))
        print(req.status_code)

        #if resource is valid
        if req.status_code == 200:
            req1 = post(f'{fhir_test_server}/Patient', headers = headers, data = json.dumps(patient.as_json()))
            print(req1.status_code)
        
        # context

        # effective[x]
        # dateTime

        msDate = fhirdate.FHIRDate("2020-02-13T12:00:00+01:00")
        medicationStatement.effectiveDateTime = msDate

        # effective[x]
        # Period
        '''
        msPeriod = prd.Period()
        msPeriod.start = fd.FHIRDate("2020-02-03T12:00:00+01:00")
        msPeriod.end = fd.FHIRDate("2020-02-04T12:00:00+01:00")
        medicationStatement.effectivePeriod = msPeriod
        '''

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
        '''
        msSiteCode = cc.CodeableConcept()
        msSiteCodeCoding = co.Coding()
        msSiteCodeCoding.system = ''
        msSiteCodeCoding.code = ''
        msSiteCodeCoding.display = ''
        msSiteCode.coding = [msSiteCodeCoding]
        msDosage.site = msSiteCode
        '''

        # Dosage.method
        '''
        msMethodCode = cc.CodeableConcept()
        msMethodCodeCoding = co.Coding()
        msMethodCodeCoding.system = ''
        msMethodCodeCoding.code = ''
        msMethodCodeCoding.display = ''
        msMethodCode.coding = [msMethodCodeCoding]
        msDosage.method = msMethodCode
        '''

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
        req = post(f'{fhir_test_server}/MedicationStatement/$validate', headers = headers, data = json.dumps(medicationStatement.as_json()))
        print(req.status_code)

        #if resource is valid
        if req.status_code == 200:
            req1 = post(f'{fhir_test_server}/MedicationStatement', headers = headers, data = json.dumps(medicationStatement.as_json()))
            print(req1.status_code)

 if __name__ == '__main__':
     ops_data = pd.read_csv('./ops_subs_merged_edit_test_neu.csv', encoding='ISO-8859-1')
