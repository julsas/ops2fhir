import logging
import os
import pathlib

import medicationgenerator


if __name__ == '__main__':
    # logging.getLogger().setLevel(logging.INFO)

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    low_val_col = 'Einheit_Wert_min'
    high_val_col = 'Einheit_Wert_max'
    numerical_cols = [low_val_col, high_val_col]
    col_names = ['ASK_Substanz_allg']
    coding_col_names = ['UNII_Substanz_allg', 'ASK_Substanz_allg', 'CAS_Substanz_allg']
    coding_display_col = 'Substanz_allg_engl_INN_oder_sonst'
    route_code_col = 'Routes and Methods of Administration - Concept Code'
    route_display_col = 'Routes and Methods of Administration - Term'
    ops_text_col = 'opsText'
    unit_code_col = 'UCUM-Code'
    unit_col = 'UCUM-Description'

    csv_cols = [
        coding_display_col,
        route_code_col,
        route_display_col,
        ops_text_col,
        unit_code_col,
        unit_col,
    ]
    csv_cols += numerical_cols
    csv_cols += coding_col_names

    # read and prepare csv with ops data
    subset = list(csv_cols)
    subset.remove(high_val_col)
    ops_csv = medicationgenerator.OpsCsvReader(
        file_path='../ops_subs_merged_edit.csv',
        encoding='ISO-8859-1',
        usecols=csv_cols,
        subset=subset
    )

    ops_csv.comma_to_dot(col_names=numerical_cols)
    ops_csv.as_str(col_names=col_names)

    med_statement_ids = medicationgenerator.generate_and_post(
        base_url='https://hdp-fhir-dev-pub.charite.de',
        # base_url='https://vonk-server.azurewebsites.net',
        verification=True,
        coding_col_names=coding_col_names,
        coding_display_col=coding_display_col,
        extension_url='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/wirkstofftyp',
        extension_system='http://www.nlm.nih.gov/research/umls/rxnorm',
        extension_code='IN',
        extension_display='ingredient',
        med_profile='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication',
        patient_profile='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Patient',
        first_names_path='../../fhir_patient_generator/input/first_names.json',
        last_names_path='../../fhir_patient_generator/input/last_names.json',
        genders_path='../../fhir_patient_generator/input/genders.json',
        postal_codes_path='../../fhir_patient_generator/input/zuordnung_plz_ort_landkreis.csv',
        name_use='official',
        ident_system='http://fhir.de/NamingSystem/gkv/kvid-10',
        ops_df=ops_csv.data,
        med_statement_profile='https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/MedicationStatement',
        country='DE',
        med_statement_status='completed',
        route_system='http://standardterms.edqm.eu',
        route_code_col=route_code_col,
        route_display_col=route_display_col,
        ops_text_col=ops_text_col,
        low_val_col=low_val_col,
        unit_code_col=unit_code_col,
        unit_col=unit_col,
        unit_system='http://unitsofmeasure.org',
        high_val_col=high_val_col
    )

    pathlib.Path('../output/posted_med_statements.txt').write_text(os.linesep.join(med_statement_ids))
