import pyodbc 
import pandas as pd
from getpass import getpass
import datetime
import numpy as np
import logging
# tested on python 3.6.9

# constants and configs
DEBUG = True

if DEBUG:
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

# methods 
def get_db_connection(user, password):
    if not user or not password:
        raise SyntaxError('username or password not set')
    try:
        #'DRIVER={FreeTDS};SERVER=yourserver.yourcompany.com;PORT=1433;DATABASE=yourdb;UID=user;PWD=password;TDS_VERSION=7.2'
        conString = ("DRIVER={ODBC Driver 17 for SQL Server};"
                    "SERVER=s-hdp-db01.charite.de;"
                    # "PORT=1433;" # default port doesn't have to be noted here 
                    "DATABASE=TBRS_CSP;"
                    f"UID={user};PWD={password};"
                    # "Trusted_Connection=no;" 
                )
        return pyodbc.connect(conString)
    except Exception as e: 
        print('error creating db connection')
        print(e)

def get_db_credentials_from_cli():
    print('Enter your credentials:')
    username = input('user: ') 
    password = getpass()
    return (username, password)


def get_case_duration_from_movements(db_connection, caseId):
    query = "" + (
        "SELECT "
        "m.RecordID "
        ",m.BWIDT "
        ",m.BWIZT "
        ",m.BWEDT "
        ",m.BWEZT "
        ",m.FALNR "
        ",m.BEWTY "
        "FROM [TBRS_CSP].[dbo].[NBEW] AS m "
        "WHERE m.FALNR = '" + caseId + "' "
        "AND STORN = '' "
    )
    logging.debug("Query: " + query)
    df = pd.read_sql_query(query, db_connection)
    # possibly analyze the given movements and just give the start and endtime of the case?
    df = convert_timestamps(df, 'BWIDT', 'BWIZT', 'BEGDT')
    df = convert_timestamps(df, 'BWEDT', 'BWEZT', 'ENDDT')

    # first debug values --> currently ignoring the end time of the movements
    return (df['BEGDT'].min(), df['BEGDT'].max())

'''
Should return about 11.891 rows.
Contain OPS Codes (6-*) from the year 2019. Those are stationary patients
by nature.
'''
def retrieve_opsdata_from_db(db_connection):
    query = "" + ( # should be 
        "SELECT " 
        # "TOP (5) " # debug 
        "f.PATNR " 
        ",f.FALNR "
        ",p.[ICPMK] "
        ",p.[ICPML] "
        ",p.[BGDOP] "
        ",p.[BZTOP] "
        ",p.[ENDOP] "
        ",p.[EZTOP] "
        # ",p.[FALNR] " # debug
        ",p.[PRTYP] "
        ",p.[QUANTITY] "
        ",p.[UNIT] "
        "FROM [TBRS_CSP].[dbo].[NFAL] AS f "
        "JOIN [TBRS_CSP].[dbo].[NICP] AS p ON p.FALNR = f.FALNR "
        "WHERE f.STORN = '' AND p.STORN = '' "
        # "AND f.BEGDT LIKE '2019%' " # can't be used since it is often just '00000000'
        "AND p.BGDOP LIKE '2019%' "
        "AND p.ICPML LIKE '6-%' "
        "AND f.FALAR = '1' "
    )
    logging.debug("Query: " + query)
    return pd.read_sql_query(query, db_connection)


def convert_timestamps(df, date_col_name, time_col_name, new_col_name):
    if DEBUG and (date_col_name not in df.columns or time_col_name not in df.columns):
        logging.debug(f"time columns not found in dataframe ({date_col_name}, {time_col_name}). Skipping...")
        return df
    df[new_col_name] = None
    for index, row in df.iterrows():
        # print(row)
        try:
            if row[time_col_name] == '240000': # yup... nessessary
                tmp_time = pd.to_datetime(row[date_col_name]+'000000', format='%Y%m%d%H%M%S')
                tmp_time = tmp_time + datetime.timedelta(days=1)
            else:
                tmp_time = pd.to_datetime(row[date_col_name]+row[time_col_name], format='%Y%m%d%H%M%S')
        except:
            tmp_time = None
        df.loc[index, new_col_name] = tmp_time
    del df[date_col_name]
    del df[time_col_name]
    return df

def quality_assurance(df):
    # make op catalogs human readable
    df = op_catalog_human_readable(df)
    df = convert_timestamps(df, 'BGDOP', 'BZTOP','BDTOP')
    df = convert_timestamps(df, 'ENDOP', 'EZTOP','EDTOP')

    return df

def op_catalog_human_readable(df):
    if 'ICPMK' in df.columns:
        for index, row in df.iterrows():
            # convert katalog info
            if row['ICPMK'] =='OI': # OI --> OPS 2018
                df.loc[index, 'ICPMK'] = "OPS 2018"
            elif row['ICPMK'] =='OJ': # OJ --> OPS 2019
                df.loc[index, 'ICPMK'] = "OPS 2019" 
            elif row['ICPMK'] =='OK': # OK --> OPS 2020
                df.loc[index, 'ICPMK'] = "OPS 2020"
            else:
                raise ValueError('unsupported operation catalog')
    return df


if __name__ == '__main__':
    db_credentials = get_db_credentials_from_cli()
    dbcon = get_db_connection(db_credentials[0], db_credentials[1])
    with dbcon:
        print("start querying operations ...")
        df = retrieve_opsdata_from_db(dbcon)
        df = quality_assurance(df)
        print("start querying movements...")
        df['movsBegin'] = None
        df['movsEnd'] = None
        for index, row in df.iterrows():
            # analyze_op_times(df)
            (mBeg, mEnd) = get_case_duration_from_movements(dbcon, row['FALNR'])
            df.loc[index, 'movsBegin'] = mBeg 
            df.loc[index, 'movsEnd'] = mEnd 
        print(df)
        # since the data drives on my dev machine are not encrypted I don't want to save it to file.
