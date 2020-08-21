import json
import logging
import tkinter as tk
from tkinter import simpledialog, messagebox

from fhirclient.models import patient

import medicationgenerator

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # User input
    flag = True
    while flag:
        window = tk.Tk()
        window.withdraw()
        user_in = simpledialog.askstring(title="FHIR Server", prompt="Enter your server's base URL:")

        if user_in == None:
            flag = False
            exit()
        elif type(user_in) == str and not user_in:
            warning = messagebox.askyesno(title='Missing entry', message='Program can\'t run without a server URL. Are you sure you want to continue?')
            if warning:
                flag = False
                exit()




    # Post example patient and get ID
    with open('Patient-example.json', 'r') as f:
        data = json.load(f)

    fhir_pat = patient.Patient(data)

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
    ops_code_col = 'opsCode'

    csv_cols = [
        coding_display_col,
        route_code_col,
        route_display_col,
        ops_text_col,
        unit_code_col,
        unit_col,
        ops_code_col
    ]
    csv_cols += numerical_cols
    csv_cols += coding_col_names

    # read and prepare csv with ops data
    subset = list(csv_cols)
    subset.remove(high_val_col)
    ops_csv = medicationgenerator.OpsCsvReader(
        file_path='ops_mapping_example.csv',
        encoding='ISO-8859-1',
        usecols=csv_cols,
        subset=subset
    )

    ops_csv.comma_to_dot(col_names=numerical_cols)
    ops_csv.as_str(col_names=col_names)

    med_statement_ids = medicationgenerator.generate_and_post(
        base_url=user_in,
        verification=True,
        coding_col_names=coding_col_names,
        coding_display_col=coding_display_col,
        extension_url='https://www.medizininformatik-initiative.de/fhir/core/modul-medikation/StructureDefinition/wirkstofftyp',
        extension_system='https://www.medizininformatik-initiative.de/fhir/core/modul-medikation/CodeSystem/wirkstofftyp',
        extension_code='IN',
        extension_display='ingredient',
        med_profile='https://www.medizininformatik-initiative.de/fhir/core/modul-medikation/StructureDefinition/Medication',
        ops_df=ops_csv.data,
        med_statement_profile='https://www.medizininformatik-initiative.de/fhir/core/modul-medikation/StructureDefinition/MedicationStatement',
        med_statement_status='completed',
        route_system='http://standardterms.edqm.eu',
        route_code_col=route_code_col,
        route_display_col=route_display_col,
        ops_text_col=ops_text_col,
        low_val_col=low_val_col,
        unit_code_col=unit_code_col,
        unit_col=unit_col,
        unit_system='http://unitsofmeasure.org',
        high_val_col=high_val_col,
        procedure_profile='https://www.medizininformatik-initiative.de/fhir/core/modul-prozedur/StructureDefinition/Procedure',
        procedure_status='completed',
        procedure_category_system='http://snomed.info/sct',
        procedure_category_code='182832007',
        procedure_category_display='Procedure related to management of drug administration (procedure)',
        procedure_ops_system='http://fhir.de/CodeSystem/dimdi/ops',
        procedure_ops_code=ops_code_col,
        procedure_ops_version='2020',
        fhir_pat=fhir_pat
    )
