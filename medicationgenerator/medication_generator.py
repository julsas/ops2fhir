from typing import List
import logging

import pandas as pd
from fhirclient.models import (
    medication,
    meta,
    extension,
    coding,
    codeableconcept
)

SYSTEM_UNII = 'http://fdasis.nlm.nih.gov'
SYSTEM_ASK = 'http://fhir.de/CodeSystem/ask'
SYSTEM_CAS = 'urn:oid:2.16.840.1.113883.6.61'

logger = logging.getLogger(__name__)

class MedIngredient:
    def __init__(self, codeable_concept, ext):
        self.codeable_concept = codeable_concept
        self.extension = ext

    def to_fhir(self) -> medication.MedicationIngredient:
        fhir_med_ingredient = medication.MedicationIngredient()
        fhir_med_ingredient.itemCodeableConcept = self.codeable_concept.to_fhir()

        fhir_med_ingredient.extension = [self.extension.to_fhir()]

        return fhir_med_ingredient


class IngredientCodeableConcept:
    def __init__(self, coding):
        self.coding = coding

    def to_fhir(self) -> codeableconcept.CodeableConcept:
        ingredient_codeable_concept = codeableconcept.CodeableConcept()
        ingredient_codeable_concept.coding = [code.to_fhir() for code in self.coding]

        return ingredient_codeable_concept


class IngredientExtension:
    def __init__(self, url, coding_system, coding_code, coding_display):
        self.url = url
        self.coding_system = coding_system
        self.coding_code = coding_code
        self.coding_display = coding_display

    def to_fhir(self) -> extension.Extension:
        ingredient_extension = extension.Extension()
        ingredient_extension.url = self.url

        extension_coding = coding.Coding()
        extension_coding.system = self.coding_system
        extension_coding.code = self.coding_code
        extension_coding.display = self.coding_display

        ingredient_extension.valueCoding = extension_coding

        return ingredient_extension


class IngredientCoding:
    def __init__(self, system, code, display):
        self.system = system
        self.code = code
        self.display = display

    def to_fhir(self) -> coding.Coding:
        ingredient_coding = coding.Coding()
        ingredient_coding.system = self.system
        ingredient_coding.code = self.code
        ingredient_coding.display = self.display

        return ingredient_coding


class Medication:
    def __init__(self, meta_profile, ingredient):
        self.meta_profile = meta_profile
        self.ingredient = ingredient

    def to_fhir(self):
        fhir_medication = medication.Medication()

        fhir_meta = meta.Meta()
        fhir_meta.profile = [self.meta_profile]
        fhir_medication.meta = fhir_meta

        fhir_medication.ingredient = [self.ingredient.to_fhir()]

        return fhir_medication


class MedicationGenerator:
    def __init__(self, coding_col_names: List[str], coding_display_col, extension_url, extension_system,
                 extension_code, extension_display, meta_profile, ops_df: pd.DataFrame):
        self.coding_col_names = coding_col_names
        self.coding_display_col = coding_display_col
        self.extension_url = extension_url
        self.extension_system = extension_system
        self.extension_code = extension_code
        self.extension_display = extension_display
        self.meta_profile = meta_profile
        self.ops_df = ops_df

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
            logger.warning(f'Failed to generate Medication: {e}')
            result = None
        finally:
            self.n += 1
            return result

    def generate(self, row):

        ingredient_ext = self.__generate_ingredient_extension()
        ingredient_codings = self.__generate_ingredient_codings(row)

        concept = IngredientCodeableConcept(coding=ingredient_codings)

        med_ingredient = MedIngredient(codeable_concept=concept, ext=ingredient_ext)

        med = Medication(
            meta_profile=self.meta_profile,
            ingredient=med_ingredient,
        )

        return med

    def __generate_ingredient_extension(self) -> IngredientExtension:
        ingredient_extension = IngredientExtension(
            url=self.extension_url,
            coding_system=self.extension_system,
            coding_code=self.extension_code,
            coding_display=self.extension_display
        )

        return ingredient_extension

    def __generate_ingredient_codings(self, row) -> List[IngredientCoding]:
        ingredient_codings = []

        display = row[self.coding_display_col]
        if display is None or type(display) != str:
            raise Exception('Display value not valid')

        for col_name in self.coding_col_names:
            code = row[col_name]
            if code is None or type(code) != str:
                continue

            col_name = col_name.lower()
            if 'unii' in col_name:
                system = SYSTEM_UNII
            elif 'ask' in col_name:
                system = SYSTEM_ASK
            elif 'cas' in col_name:
                system = SYSTEM_CAS
            else:
                raise ValueError('invalid system')

            ingredient_coding = IngredientCoding(
                code=code,
                display=display,
                system=system
            )

            ingredient_codings.append(ingredient_coding)

        if not ingredient_codings:
            raise Exception('There are no values for ingredient codings')

        return ingredient_codings
