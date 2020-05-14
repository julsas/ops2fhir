from fhirclient.models import (
    procedure,
    coding,
    meta,
    codeableconcept,
    period,
    fhirdate,
    extension,
    fhirreference
)

from patientgenerator import client

class CategoryCoding:
    def __init__(self, system, code, display):
        self.system = system
        self.code = code
        self.display = display

    def to_fhir(self) -> coding.Coding:
        fhir_coding = coding.Coding()
        fhir_coding.system = self.system
        fhir_coding.code = self.code
        fhir_coding.display = self.display

        return fhir_coding

class Category:
    def __init__(self, category_coding):
        self.category_coding = category_coding

    def to_fhir(self) -> codeableconcept.CodeableConcept:
        fhir_category = codeableconcept.CodeableConcept()
        fhir_category.coding = [code.to_fhir() for code in self.category_coding]

        return fhir_category


class ProcedureCodeableConcept:
    def __init__(self, procedure_coding):
        self.procedure_coding = procedure_coding

    def to_fhir(self) -> codeableconcept.CodeableConcept:
        procedure_code = codeableconcept.CodeableConcept()
        procedure_code.coding = [code.to_fhir() for code in self.procedure_coding]

        return procedure_code

class ProcedureCoding:
    def __init__(self, system, code, display):
        self.system = system
        self.code = code
        self.display = display

    def to_fhir(self) -> coding.Coding:
        fhir_coding = coding.Coding()
        fhir_coding.system = self.system
        fhir_coding.code = self.code
        fhir_coding.display = self.display

        return fhir_coding

class FhirPeriod:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def to_fhir(self) -> period.Period:
        fhir_period = period.Period()
        fhir_period.start = self.start.to_fhir()
        fhir_period.end = self.end.to_fhir()

        return fhir_period


class FhirDatetime:
    def __init__(self, date_time):
        self.date_time = date_time

    def to_fhir(self) -> fhirdate.FHIRDate:
        fhir_date = fhirdate.FHIRDate()
        fhir_date.date = self.date_time

        return fhir_date

# optional extension
class RecordedDate:
    def __init__(self, recorded_datetime):
        self.recorded_datetime = recorded_datetime

    def to_fhir(self) -> extension.Extension:
        fhir_extension = extension.Extension()
        fhir_extension.url = 'https://simplifier.net/MedizininformatikInitiative-ModulProzeduren/procedure-recordedDate'
        fhir_extension.valueDateTime = self.recorded_datetime.to_fhir()

        return fhir_extension

# optional extension
class ProcedureIntention:
    def __init__(self, system, code, display):
        self.system = system
        self.code = code
        self.display = display

    def to_fhir(self) -> extension.Extension:
        fhir_extension = extension.Extension()
        fhir_extension.url = 'https://simplifier.net/MedizininformatikInitiative-ModulProzeduren/Durchfuehrungsabsicht'

        fhir_coding = coding.Coding()
        fhir_coding.system = self.system
        fhir_coding.code = self.code
        fhir_coding.display = self.display
        fhir_extension.valueCoding = fhir_coding

        return fhir_extension


class Reference:
    def __init__(self, id, resource_type: client.ResourceEnum):
        self.id = id
        self.resource_type = resource_type

    def to_fhir(self):
        fhir_reference = fhirreference.FHIRReference()
        fhir_reference.reference = f'{self.resource_type.value}/{self.id}'

        return fhir_reference


class Procedure:
    def __init__(self, profile_url, status, category, procedure_code, pat_reference, performed):
        self.profile_url = profile_url
        self.status = status
        self.category = category
        self.procedure_code = procedure_code
        self.pat_reference = pat_reference
        self.performed = performed

    def to_fhir(self) -> procedure.Procedure:
        fhir_procedure = procedure.Procedure()

        fhir_meta = meta.Meta()
        fhir_meta.profile = self.profile_url
        fhir_procedure.meta = fhir_meta

        fhir_procedure.status = self.status
        fhir_procedure.category = self.category.to_fhir()
        fhir_procedure.code = self.procedure_code.to_fhir()
        fhir_procedure.subject = self.pat_reference.to_fhir()

        if type(self.performed) == FhirDatetime:
            fhir_procedure.performedDateTime = self.performed.to_fhir()
        elif type(self.performed) == FhirPeriod:
            fhir_procedure.performedPeriod = self.performed.to_fhir()

        return fhir_procedure


class ProcedureGenerator:
    def __init__(self, profile_url, status, category_system, category_code, category_display, ops_system, ops_code, ops_display, performed_timestamp, db_data):
        self.profile_url = profile_url
        self.status = status
        self.category_system = category_system
        self.category_code = category_code
        self.category_display = category_display
        self.ops_system = ops_system
        self.ops_code = ops_code
        self.ops_display = ops_display
        self.performed_timestamp = performed_timestamp
        self.db_data = db_data

    def generate(self, pat_id):
        generated_procedure = Procedure(
            profile_url=self.profile_url,
            status=self.status,

        )