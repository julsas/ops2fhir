import json
import logging
import pathlib

from patientgenerator import client, mypatient

from medicationgenerator import medication_generator, med_statement

logger = logging.getLogger(__name__)


def generate_and_post(base_url, verification, ops_df, coding_col_names, coding_display_col, extension_url,
                      extension_system, extension_code, extension_display, med_profile, med_statement_profile,
                      patient_profile, last_names_path, first_names_path, genders_path, postal_codes_path, name_use,
                      ident_system, country, med_statement_status, route_system, route_code_col,
                      route_display_col, ops_text_col, low_val_col, unit_code_col, unit_col, unit_system, high_val_col):
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

    last_names_path = pathlib.Path(last_names_path).absolute()
    first_names_path = pathlib.Path(first_names_path).absolute()
    genders_path = pathlib.Path(genders_path).absolute()

    pat_generator = mypatient.PatientGenerator(
        profile_url=patient_profile,
        last_names_path=last_names_path,
        first_names_path=first_names_path,
        genders_path=genders_path,
        postal_codes_path=postal_codes_path,
        name_use=name_use,
        ident_system=ident_system,
        country=country,
        num_pat=len(ops_df)
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

    vonk_client = client.VonkClient(base_url, verification)

    pat_iter = iter(pat_generator)

    med_stat_ids = []
    n_rows = len(ops_df)
    n_row = 0
    for row in ops_df.iterrows():
        try:
            med = med_generator.generate(row[1]).to_fhir()
        except Exception as e:
            logger.error(f'Could not create Medication resource: {e}')
            continue
        response = vonk_client.post_resource(med, client.ResourceEnum.MEDICATION, validate_flag=True)

        med_id = json.loads(response.text)['id']

        try:
            pat = next(pat_iter).to_fhir()
        except Exception as e:
            logger.error(f'Could not create Patient resource: {e}')
            continue
        response = vonk_client.post_resource(pat, client.ResourceEnum.PATIENT, validate_flag=True)

        pat_id = json.loads(response.text)['id']

        try:
            med_stat = med_statement_generator.generate(row[1], med_id, pat_id).to_fhir()
        except Exception as e:
            logger.error(f'Could not create MedicationStatement resource: {e}')
            continue
        response = vonk_client.post_resource(med_stat, client.ResourceEnum.MEDSTATEMENT, validate_flag=True)

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

        # response = vonk_client.post_resource(fhir_med, client.ResourceEnum.MEDICATION, False)
        # if response.status_code != 201:
        #    raise Exception(f'Failed to post medication: {response.content}')

        response_text = json.loads(response.text)
        med_id = response_text['id']
        # print(f'Posted Medication: {med_id}')
        med_ids.append(med_id)

    print(f'Posted {med_ids.__len__()} Medication resources!')

    return med_ids
