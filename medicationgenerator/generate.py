import json
import logging
import pathlib

from medicationgenerator import medication_generator, med_statement
from proceduregenerator import procedure_generator

logger = logging.getLogger(__name__)


def generate_and_post(base_url, verification, ops_df, coding_col_names, coding_display_col, extension_url,
                      extension_system, extension_code, extension_display, med_profile, med_statement_profile,
                      med_statement_status, route_system, route_code_col, route_display_col, ops_text_col, low_val_col,
                      unit_code_col, unit_col, unit_system, high_val_col, procedure_profile, procedure_status,
                      procedure_category_system, procedure_category_code, procedure_category_display,
                      procedure_ops_system, procedure_ops_code, fhir_pat, procedure_ops_version_col=None,
                      procedure_ops_version=None, performed_start_col=None, performed_end_col=None):
    med_generator = medication_generator.MedicationGenerator(
        coding_col_names=coding_col_names,
        coding_display_col=coding_display_col,
        extension_url=extension_url,
        extension_system=extension_system,
        extension_code=extension_code,
        extension_display=extension_display,
        meta_profile=med_profile,
        ops_df=ops_df
    )

    proc_generator = procedure_generator.ProcedureGenerator(
        profile_url=procedure_profile,
        status=procedure_status,
        category_system=procedure_category_system,
        category_code=procedure_category_code,
        category_display=procedure_category_display,
        ops_system=procedure_ops_system,
        ops_code_col=procedure_ops_code,
        ops_display_col=ops_text_col,
        ops_version=procedure_ops_version,
        ops_version_col=procedure_ops_version_col,
        performed_start_col=performed_start_col,
        performed_end_col=performed_end_col
    )

    med_statement_generator = med_statement.MedStatementGenerator(
        profile_url=med_statement_profile,
        status=med_statement_status,
        route_system=route_system,
        route_code_col=route_code_col,
        route_display_col=route_display_col,
        ops_text_col=ops_text_col,
        low_val_col=low_val_col,
        unit_code_col=unit_code_col,
        unit_col=unit_col,
        unit_system=unit_system,
        high_val_col=high_val_col,
        ops_df=ops_df
    )

    fhir_client = client.VonkClient(base_url, verification)

    med_stat_ids = []
    n_rows = len(ops_df)
    n_row = 0
    pat_id = json.loads(fhir_pat)['id']
    for row in ops_df.iterrows():
        try:
            med = med_generator.generate(row[1]).to_fhir()
        except Exception as e:
            logger.error(f'Could not create Medication resource: {e}')
            continue
        response = fhir_client.post_resource(med, client.ResourceEnum.MEDICATION, validate_flag=True)

        med_id = json.loads(response.text)['id']

        try:
            proc = proc_generator.generate(row[1], pat_id=pat_id).to_fhir()
        except Exception as e:
            logger.error(f'Could not create Procedure resource: {e}')
            continue
        response = fhir_client.post_resource(proc, client.ResourceEnum.PROCEDURE, validate_flag=True)

        proc_id = json.loads(response.text)['id']

        try:
            med_stat = med_statement_generator.generate(row[1], med_id, pat_id, proc_id).to_fhir()
        except Exception as e:
            logger.error(f'Could not create MedicationStatement resource: {e}')
            continue
        response = fhir_client.post_resource(med_stat, client.ResourceEnum.MEDSTATEMENT, validate_flag=True)

        med_stat_id = json.loads(response.text)['id']
        med_stat_ids.append(med_stat_id)

        n_row += 1
        print(f'Processed {n_row}/{n_rows}')

    return med_stat_ids


def generate_and_post_medications(base_url, verification, coding_col_names, coding_display_col, extension_url,
                                  extension_system, extension_code, extension_display, meta_profile, ops_df):
    generator = medication_generator.MedicationGenerator(
        coding_col_names=coding_col_names,
        coding_display_col=coding_display_col,
        extension_url=extension_url,
        extension_system=extension_system,
        extension_code=extension_code,
        extension_display=extension_display,
        meta_profile=meta_profile,
        ops_df=ops_df
    )

    vonk_client = client.VonkClient(base_url, verification)
    med_ids = []

    for med in generator:
        if not med:
            continue

        fhir_med = med.to_fhir()
        response = vonk_client.post_resource(fhir_med, client.ResourceEnum.MEDICATION, True)

        if response.status_code != 200:
            raise Exception(f'Failed to validate medication: {response.content}')

        response_text = json.loads(response.text)
        med_id = response_text['id']
        # print(f'Posted Medication: {med_id}')
        med_ids.append(med_id)

    print(f'Posted {med_ids.__len__()} Medication resources!')

    return med_ids


def generate_and_post_procedure(base_url, verification, profile_url, status, category_system, category_code,
                                category_display, ops_system, ops_code_col, ops_display_col, ops_df, fhir_pat,
                                ops_version_col=None, ops_version=None, performed_start_col=None,
                                performed_end_col=None):

    proc_generator = procedure_generator.ProcedureGenerator(
        profile_url=profile_url,
        status=status,
        category_system=category_system,
        category_code=category_code,
        category_display=category_display,
        ops_system=ops_system,
        ops_code_col=ops_code_col,
        ops_version_col=ops_version_col,
        ops_version=ops_version,
        ops_display_col=ops_display_col,
        performed_start_col=performed_start_col,
        performed_end_col=performed_end_col
    )

    vonk_client = client.VonkClient(base_url, verification)
    procedure_ids = []
    n_rows = len(ops_df)
    n_row = 0
    pat_id = json.loads(fhir_pat)['id']

    for row in ops_df.iterrows():

        try:
            generated_procedure = proc_generator.generate(row[1], pat_id).to_fhir()
        except Exception as e:
            logger.error(f'Could not create Procedure resource: {e}')
            continue
        response = vonk_client.post_resource(generated_procedure, client.ResourceEnum.PROCEDURE, validate_flag=True)

        procedure_id = json.loads(response.text)['id']
        procedure_ids.append(procedure_id)

        n_row += 1
        print(f'Processed {n_row}/{n_rows}')

    return procedure_ids
