import logging
from typing import List

import pandas as pd
from fhirclient.models import (
    medicationstatement,
    meta,
    fhirreference,
    dosage,
    codeableconcept,
    coding,
    range,
    quantity,
    period,
    fhirdate
)
from patientgenerator import client, generator_helpers

logger = logging.getLogger(__name__)


class RouteCoding:
    def __init__(self, system, code, display):
        self.system = system
        self.code = code
        self.display = display

    def to_fhir(self):
        route_coding = coding.Coding()
        route_coding.system = self.system
        route_coding.code = self.code
        route_coding.display = self.display

        return route_coding


class RouteCodeableConcept:
    def __init__(self, coding):
        self.coding = coding

    def to_fhir(self):
        route_code = codeableconcept.CodeableConcept()
        route_code.coding = [route_coding.to_fhir() for route_coding in self.coding]

        return route_code


class MedQuantity:
    def __init__(self, value, unit, system, code):
        self.value = value
        self.unit = unit
        self.system = system
        self.code = code

    def to_fhir(self):
        med_quantity = quantity.Quantity()
        med_quantity.value = self.value
        med_quantity.unit = self.unit
        med_quantity.system = self.system
        med_quantity.code = self.code

        return med_quantity


class MedDoseRange:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def to_fhir(self):
        dose_range = range.Range()
        dose_range.low = self.low.to_fhir()
        dose_range.high = self.high.to_fhir()

        return dose_range


class MedDoseAndRate:
    def __init__(self, quantity):
        self.quantity = quantity

    def to_fhir(self):
        dose_and_rate = dosage.DosageDoseAndRate()
        if type(self.quantity) == MedQuantity:
            dose_and_rate.doseQuantity = self.quantity.to_fhir()
        elif type(self.quantity) == MedDoseRange:
            dose_and_rate.doseRange = self.quantity.to_fhir()
        else:
            raise Exception('Wrong datatype for dose quantity')

        return dose_and_rate


class MedDosage:
    def __init__(self, ops_text, route_code, dose_and_rate):
        self.text = ops_text
        self.route = route_code
        self.dose_and_rate = dose_and_rate

    def to_fhir(self):
        fhir_dosage = dosage.Dosage()
        fhir_dosage.text = self.text
        fhir_dosage.route = self.route.to_fhir()
        fhir_dosage.doseAndRate = [self.dose_and_rate.to_fhir()]

        return fhir_dosage


class FhirDateTime:
    def __init__(self, random_date):
        self.random_date = random_date

    def to_fhir(self):
        fhir_date = fhirdate.FHIRDate()
        fhir_date.date = self.random_date

        return fhir_date


class EffectivePeriod:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def to_fhir(self):
        effective_period = period.Period()
        effective_period.start = self.start
        effective_period.end = self.end

        return effective_period


class Reference:
    def __init__(self, id, resource_type: client.ResourceEnum):
        self.id = id
        self.resource_type = resource_type

    def to_fhir(self):
        fhir_reference = fhirreference.FHIRReference()
        fhir_reference.reference = f'{self.resource_type.value}/{self.id}'

        return fhir_reference


class MedStatementGenerator:
    def __init__(self, profile_url, part_of, status, route_system, route_code_col, route_display_col, ops_text_col,
                 low_val_col, unit_code_col, unit_col, unit_system, high_val_col, ops_df: pd.DataFrame):
        self.profile_url = profile_url
        self.part_of = part_of
        self.status = status
        self.route_system = route_system
        self.route_code_col = route_code_col
        self.route_display_col = route_display_col
        self.ops_text_col = ops_text_col
        self.low_val_col = low_val_col
        self.unit_code_col = unit_code_col
        self.unit_col = unit_col
        self.unit_system = unit_system
        self.high_val_col = high_val_col

        self.ops_df = ops_df

        self.date_generator = generator_helpers.RandomDates()

    def __iter__(self):
        self.n = 0
        self.ops_df_iter = self.ops_df.iterrows()
        return self

    def __next__(self):
        if self.n >= len(self.ops_df):
            raise StopIteration

        try:
            result = self.generate(next(self.ops_df_iter)[1])
        except Exception as e:
            logger.warning(f'Failed to generate MedicationStatement: {e}')
            result = None
        finally:
            self.n += 1
            return result

    def generate(self, row, med_id, pat_id, proc_id):
        route_coding = self.__generate_route_coding(
            row=row,
            system=self.route_system,
            code_col=self.route_code_col,
            display_col=self.route_display_col
        )
        route_code = RouteCodeableConcept(route_coding)

        dose_quantity = self.__generate_quantity(
            row=row,
            low_val_col=self.low_val_col,
            unit_col=self.unit_col,
            unit_system=self.unit_system,
            unit_code_col=self.unit_code_col,
            high_val_col=self.high_val_col
        )
        dose_and_rate = MedDoseAndRate(
            quantity=dose_quantity
        )

        med_dosage = MedDosage(
            ops_text=row[self.ops_text_col],
            route_code=route_code,
            dose_and_rate=dose_and_rate
        )

        med_reference = Reference(
            id=med_id,
            resource_type=client.ResourceEnum.MEDICATION
        )

        pat_reference = Reference(
            id=pat_id,
            resource_type=client.ResourceEnum.PATIENT
        )

        proc_reference = Reference(
            id=proc_id,
            resource_type=client.ResourceEnum.PROCEDURE
        )

        # TODO: generate effective period, tmp datetime instead of period!!
        random_date = self.date_generator.next()
        fhir_date = FhirDateTime(random_date)

        med_statement = MedicationStatement(
            profile_url=self.profile_url,
            status=self.status,
            med_reference=med_reference,
            pat_reference=pat_reference,
            timestamp=fhir_date,
            dosage=med_dosage
        )

        return med_statement

    def __generate_route_coding(self, row, system, code_col, display_col) -> List[RouteCoding]:

        route_coding = RouteCoding(
            system=system,
            code=str(row[code_col]),
            display=str(row[display_col])
        )

        return [route_coding]

    def __generate_quantity(self, row, low_val_col, unit_col, unit_system, unit_code_col, high_val_col):

        if not row[low_val_col]:
            raise Exception(f'Missing value for dose quantity')
        elif not row[unit_code_col]:
            raise Exception(f'Missing code for dose quantity')
        elif not row[unit_col]:
            raise Exception(f'Missing unit for dose quantity')

        dose_quantity = MedQuantity(
            value=row[low_val_col],
            unit=row[unit_col],
            system=unit_system,
            code=row[unit_code_col]
        )

        if not (pd.isnull(row[high_val_col])):
            low = dose_quantity
            if not isinstance(row[unit_col], str):
                raise Exception('Unit has wrong data type')

            if not isinstance(row[unit_code_col], str):
                raise Exception('Unit code has wrong data type')

            high = MedQuantity(
                value=row[high_val_col],
                unit=row[unit_col],
                system=unit_system,
                code=row[unit_code_col]
            )
            dose_quantity = MedDoseRange(
                low=low,
                high=high
            )

        return dose_quantity

    def __generate_range_values(self, row, value_col, unit_col, system, code_col):
        if not isinstance(row[unit_col], str):
            raise Exception('Unit has wrong data type')

        if not isinstance(row[code_col], str):
            raise Exception('Unit code has wrong data type')

        range_quantity = MedQuantity(
            value=row[value_col],
            unit=row[unit_col],
            system=system,
            code=row[code_col]
        )

        return range_quantity


class MedicationStatement:
    def __init__(self, profile_url, part_of, status, med_reference, pat_reference, timestamp, dosage):
        self.profile_url = profile_url
        self.part_of = part_of
        self.status = status
        self.med_reference = med_reference
        self.pat_reference = pat_reference
        self.timestamp = timestamp
        self.dosage = dosage

    def to_fhir(self) -> medicationstatement.MedicationStatement:
        fhir_med_statement = medicationstatement.MedicationStatement()

        fhir_meta = meta.Meta()
        fhir_meta.profile = [self.profile_url]
        fhir_med_statement.meta = fhir_meta

        fhir_med_statement.partOf = self.part_of.to_fhir()

        fhir_med_statement.status = self.status

        fhir_med_statement.medicationReference = self.med_reference.to_fhir()
        fhir_med_statement.subject = self.pat_reference.to_fhir()

        if type(self.timestamp) == EffectivePeriod:
            fhir_med_statement.effectivePeriod = self.timestamp.to_fhir()
        elif type(self.timestamp) == FhirDateTime:
            fhir_med_statement.effectiveDateTime = self.timestamp.to_fhir()

        fhir_med_statement.dosage = [self.dosage.to_fhir()]

        return fhir_med_statement
