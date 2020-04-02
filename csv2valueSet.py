#%%
import json
import pandas as pd
import numpy as np 
import fhirclient
import fhirclient.models.valueset as vs
import fhirclient.models.meta as ma
import fhirclient.models.fhirdate as fd

# %%
ops_data = pd.read_csv('./ops_subs_merged_edit.csv', encoding = 'ISO-8859-1')

# %%
ops_data.head()

# %%
# for index, row in ops_data.iterrows():

# %%
valueSet = vs.ValueSet()
vsMeta = ma.Meta()
vsMeta.profile = "http://hl7.org/fhir/StructureDefinition/shareablevalueset"
valueSet.url = "https://www.medizininformatik-initiative.de/fhir/core/ValueSet/ops-ask-ingredients"
valueSet.name = "ops-ask-codes"
valueSet.status = "draft"
valueSet.experimental = True
vsDate = fd.FHIRDate("2020-04-02")
valueSet.date = vsDate
valueSet.publisher = "https://www.medizininformatik-initiative.de"
valueSet.description = "Enthaelt alle ASK Codes aus dem OPS Mapping"
vsCompose = vs.ValueSetCompose()
vsci = vs.ValueSetComposeInclude()
vsci.system = "http://fhir.de/CodeSystem/ask"
vscic = vs.ValueSetComposeIncludeConcept()
concepts = []
for index, row in ops_data.iterrows():
    vscic.code = f'{row[41]}'
    vscic.display = f'{row[32]}'
    concepts.append(vscic)
    
vsci.concept = [vscic]
valueSet.compose = vsCompose

fname = 'valueSet-ops-ask.json'
with open(fname, 'w') as outfile:
    json.dump(valueSet.as_json(), outfile, indent=4)
print("ValueSet json written to file {fn}".format(fn=fname))

# %%
for eproperty in valueSet.elementProperties():
    print(eproperty)


# %%
for eproperty in vsCompose.elementProperties():
    print(eproperty)

# %%
for eproperty in vsMeta.elementProperties():
    print(eproperty)


# %%
for eproperty in vsci.elementProperties():
    print(eproperty)

# %%
for eproperty in vscic.elementProperties():
    print(eproperty)

# %%
