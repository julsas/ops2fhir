from fhirclient.models import (
    medicationstatement,
    meta,
    fhirreference,
    dosage,
    codeableconcept,
    coding,
    range,
    quantity,
    period
)

from patientgenerator import client


class RouteCoding:
    def __init__(self):
        self.system = None
        self.code = None
        self.display = None

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
    def __init__(self):
        self.value = None
        self.unit = None
        self.system = None
        self.code = None

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
    def __init__(self, dose_range):
        self.dose_range = dose_range

    def to_fhir(self):
        dose_and_rate = dosage.DosageDoseAndRate()
        dose_and_rate.doseRange = self.dose_range.to_fhir()

        return dose_and_rate


class MedDosage:
    def __init__(self):
        self.text = None
        self.route = None
        self.dose_and_rate = None

    def to_fhir(self):
        fhir_dosage = dosage.Dosage()
        fhir_dosage.text = self.text
        fhir_dosage.route = self.route.to_fhir()
        fhir_dosage.doseAndRate = [self.dose_and_rate.to_fhir()]

        return fhir_dosage


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


class MedicationStatement:
    def __init__(self):
        self.meta_profile = None
        self.status = None
        self.med_reference = None
        self.pat_reference = None
        self.effective_period = None
        self.dosage = None

    def to_fhir(self) -> medicationstatement.MedicationStatement:
        fhir_med_statement = medicationstatement.MedicationStatement()

        fhir_meta = meta.Meta()
        fhir_meta.profile = [self.meta_profile]
        fhir_med_statement.meta = fhir_meta

        fhir_med_statement.status = self.status

        fhir_med_statement.medicationReference = self.med_reference.to_fhir()
        fhir_med_statement.subject = self.pat_reference.to_fhir()

        fhir_med_statement.effectivePeriod = self.effective_period.to_fhir()

        fhir_med_statement.dosage = [self.dosage.to_fhir()]

        return fhir_med_statement
