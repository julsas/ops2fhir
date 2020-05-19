import logging

import pandas as pd

import medicationgenerator

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    ops_display_col = 'opsText'
    ops_code_col = 'opsCode'
    file_path = 'ops_subs_merged_edit.csv'
    encoding = 'ISO-8859-1'
    usecols = [ops_display_col, ops_code_col]
    ops_df = pd.read_csv(file_path, encoding=encoding, usecols=usecols)
    ops_df = ops_df.dropna()

    procedure_ids = medicationgenerator.generate_and_post_procedure(
        base_url='https://hdp-fhir-dev-pub.charite.de',
        verification=True,
        profile_url='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Procedure',
        status='completed',
        category_system='http://snomed.info/sct',
        category_code='182832007',
        category_display='Procedure related to management of drug administration (procedure)',
        ops_system='http://fhir.de/CodeSystem/dimdi/ops',
        ops_code_col=ops_code_col,
        ops_version='2020',
        ops_display_col=ops_display_col,
        ops_df=ops_df,
        patient_profile='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Patient',
        first_names_path='../fhir_patient_generator/input/first_names.json',
        last_names_path='../fhir_patient_generator/input/last_names.json',
        genders_path='../fhir_patient_generator/input/genders.json',
        postal_codes_path='../fhir_patient_generator/input/zuordnung_plz_ort_landkreis.csv',
        name_use='official',
        ident_system='http://fhir.de/NamingSystem/gkv/kvid-10',
        country='DE'
    )
