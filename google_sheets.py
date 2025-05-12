# google_sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Definir el alcance para Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def connect_to_sheet(secret_dict, sheet_key):
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(secret_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(sheet_key)
    return sheet

def read_sheet_as_df(sheet, tab_name):
    worksheet = sheet.worksheet(tab_name)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def write_df_to_sheet(sheet, tab_name, df):
    worksheet = sheet.worksheet(tab_name)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
