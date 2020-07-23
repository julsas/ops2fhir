import logging

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

from medicationgenerator import generator_helpers

logger = logging.getLogger(__name__)


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
        fhir_category.coding = [self.category_coding.to_fhir()]

        return fhir_category


class ProcedureCodeableConcept:
    def __init__(self, procedure_coding):
        self.procedure_coding = procedure_coding

    def to_fhir(self) -> codeableconcept.CodeableConcept:
        procedure_code = codeableconcept.CodeableConcept()
        procedure_code.coding = [self.procedure_coding.to_fhir()]

        return procedure_code


class ProcedureCoding:
    def __init__(self, system, code, version, display):
        self.system = system
        self.code = code
        self.version = version
        self.display = display

    def to_fhir(self) -> coding.Coding:
        fhir_coding = coding.Coding()
        fhir_coding.system = self.system
        fhir_coding.code = self.code
        fhir_coding.version = self.version
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
        fhir_meta.profile = [self.profile_url]
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
    def __init__(self, profile_url, status, category_system, category_code, category_display, ops_system, ops_code_col,
                 ops_display_col, performed_start_col=None, performed_end_col=None, ops_version_col=None, ops_version=None):
        self.profile_url = profile_url
        self.status = status
        self.category_system = category_system
        self.category_code = category_code
        self.category_display = category_display
        self.ops_system = ops_system
        self.ops_code_col = ops_code_col
        self.ops_version_col = ops_version_col
        self.ops_version = ops_version
        self.ops_display_col = ops_display_col
        self.performed_start_col = performed_start_col
        self.performed_end_col = performed_end_col

    def generate(self, row, pat_id) -> Procedure:
        category = self.__generate_category(
            system=self.category_system,
            code=self.category_code,
            display=self.category_display
        )

        procedure_code = self.__generate_procedure_code(
            row=row,
            system=self.ops_system,
            code_col=self.ops_code_col,
            version_col=self.ops_version_col,
            version=self.ops_version,
            display_col=self.ops_display_col
        )

        subject = Reference(
            id=pat_id,
            resource_type=client.ResourceEnum.PATIENT
        )

        performed = self.__generate_performed(
            row=row,
            start_col=self.performed_start_col,
            end_col=self.performed_end_col
        )

        generated_procedure = Procedure(
            profile_url=self.profile_url,
            status=self.status,
            category=category,
            procedure_code=procedure_code,
            pat_reference=subject,
            performed=performed
        )

        return generated_procedure

    def __generate_category(self, system, code, display):
        category_coding = CategoryCoding(
            system=system,
            code=code,
            display=display
        )

        category = Category(
            category_coding
        )

        return category

    def __generate_procedure_code(self, row, system, code_col, version, version_col, display_col):
        # the version can either be a string with the OPS version or the name of the column where the version is stored
        if version:
            if version_col:
                raise Exception(
                    'Function only needs either the OPS version or the column where the version is stored in the DataFrame')
            else:
                code_version = version
        else:
            if version_col:
                code_version = row[version_col]
            else:
                raise Exception('Missing argument for OPS version')

        if not (display_col):
            procedure_coding = ProcedureCoding(
                system=system,
                code=row[code_col],
                version=code_version
            )
        elif type(display_col) == str:
            procedure_coding = ProcedureCoding(
                system=system,
                code=row[code_col],
                version=code_version,
                display=row[display_col]
            )

        procedure_code = ProcedureCodeableConcept(
            procedure_coding=procedure_coding
        )

        return procedure_code

    def __generate_performed(self, row, start_col, end_col):
        if not (start_col) and not (end_col):
            # generate one random datetime
            datetime_generator = generator_helpers.RandomDates()
            performed = FhirDatetime(
                date_time=datetime_generator.next()
            )
        else:
            start_datetime = FhirDatetime(
                date_time=row[start_col]
            )
            end_datetime = FhirDatetime(
                date_time=row[end_col]
            )
            performed = FhirPeriod(
                start=start_datetime,
                end=end_datetime
            )

        return performed
