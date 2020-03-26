import medicationgenerator

if __name__ == '__main__':
    # read and prepare csv with ops data
    ops_csv = medicationgenerator.OpsCsvReader('../ops_subs_merged_edit.csv', 'ISO-8859-1')
    numerical_cols = ['Einheit_Wert_min', 'Einheit_Wert_max']
    ops_csv.comma_to_dot(col_names=numerical_cols)
    col_names = ['ASK_Substanz_allg']
    ops_csv.as_str(col_names=col_names)

    medicationgenerator.generate_and_post_medications(
        base_url= 'https://hdp-fhir-dev-pub.charite.de',
        verification= True,
        meta_profile= 'https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/Medication',
        coding_col_names= ['UNII_Substanz_allg', 'ASK_Substanz_allg', 'CAS_Substanz_allg'],
        coding_display_col= 'Substanz_allg_engl_INN_oder_sonst',
        extension_url= 'https://www.medizininformatik-initiative.de/fhir/core/StructureDefinition/wirkstofftyp',
        extension_system= 'http://www.nlm.nih.gov/research/umls/rxnorm',
        extension_code= 'IN',
        extension_display= 'ingredient',
        ops_df= ops_csv.data
    )