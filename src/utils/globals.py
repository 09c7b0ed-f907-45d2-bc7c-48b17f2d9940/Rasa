import os
import datetime

PATH_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_RESOURCES = f"{PATH_PROJECT}\\resources"
PATH_DATA_FILE = f"{PATH_RESOURCES}\\data\\data.csv"
PATH_SAVE_PLOT = f"{PATH_RESOURCES}\\plot"
PATH_SAVE_OBJECT = f"{PATH_RESOURCES}\\object\\plot.obj"

DATE_TIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

ACCEPTED_COMPARISON_VALUES = {
    "gender": {
        "values": [0, 1],
        "labels": ["Female", "Male"]
    },
    "discharge_mrs": {
        "values": [0, 1, 2, 3, 4, 5, 6],
        "labels": ["0", "1", "2", "3", "4", "5", "6"]
    },
    "three_m_mrs": {
        "values": [0, 1, 2, 3, 4, 5, 6],
        "labels": ["0", "1", "2", "3", "4", "5", "6"]
    },
    "prenotification": {
        "values": [0, 1],
        "labels": ["Not prenotified", "Prenotified"]
    },
    "imaging_done": {
        "values": [0, 1],
        "labels": ["Imagging not done", "Imaging done"]
    },
    "occup_physiotherapy_received": {
        "values": [0, 1],
        "labels": ["Physio not started", "Physio started"]
    },
    "dysphagia_screening_done": {
        "values": [0, 1],
        "labels": ["Dysphagia not screened", "Dysphagia screening done"]
    }
}
ACCEPTED_SELECTED_VALUES = {
    "age": "Age",
    "gender": "Gender",
    "discharge_mrs": "mRS on discharge",
    "three_m_mrs": "3-month mRS",
    "prenotification": "Arrival pre-notified",
    "imaging_done": "Imaging done",
    "occup_physiotherapy_received": "Physiotherapy initiated",
    "dysphagia_screening_done": "Test for dysphagia screen",
    "nihss_score": "Nihss Score",
    "door_to_needle": "Door To Needle",
    "door_to_groin": "Door To Groin",
    "door_to_imaging": "Door To Imaging",
    "onset_to_door": "Onset To Door",
    "discharge_nihss_score": "Discharge Nihss Score",
    "glucose": "Glucose",
    "cholesterol": "Cholesterol",
    "sys_blood_pressure": "Sys Blood Pressure",
    "prestroke_mrs": "Prestroke Mrs",
    "dis_blood_pressure": "Dis Blood Pressure",
    "perfusion_core": "Perfusion Core",
    "hypoperfusion_core": "Hypoperfusion Core",
    "bleeding_volume_value": "Bleeding Volume Value",
    "hospital_stroke": "Hospital Stroke",
    "risk_previous_ischemic_stroke": "Risk Previous Ischemic Stroke",
    "risk_previous_hemorrhagic_stroke": "Risk Previous Hemorrhagic Stroke",
    "physiotherapy_start_within_3days": "Physiotherapy Start Within 3days",
    "risk_hypertension": "Risk Hypertension",
    "risk_diabetes": "Risk Diabetes",
    "ich_score": "Ich Score",
    "thrombolysis": "Thrombolysis"
}
ACCEPTED_FILTER_VALUES = {
    "QI": {
        "type": str,
        "default_value": "age",
        "accepted_values": ["age", "nihss_score", "door_to_needle", "door_to_groin", "door_to_imaging", "onset_to_door", "discharge_nihss_score", "glucose", "cholesterol", "sys_blood_pressure", "prestroke_mrs", "dis_blood_pressure", "perfusion_core", "hypoperfusion_core", "bleeding_volume_value", "discharge_mrs", "three_m_mrs", "gender", "hospital_stroke", "dysphagia_screening_done", "risk_previous_ischemic_stroke", "risk_previous_hemorrhagic_stroke", "physiotherapy_start_within_3days", "occup_physiotherapy_received", "risk_hypertension", "risk_diabetes", "prenotification", "imaging_done", "ich_score", "thrombolysis"]
    },
    "site_name": {
        "type": list,
        "default_value": [],
        "accepted_values": ["General", "Hope", "Paradise", "Rose", "Angelvale", "Mercy"]
    },
    "gender": {
        "type": list,
        "default_value": [False, True],
        "accepted_values": [False, True, 0, 1]
    },
    "imagine_done": {
        "type": list,
        "default_value": [False, True],
        "accepted_values": [False, True, 0, 1]
    },
    "prenotification": {
        "type": list,
        "default_value": [False, True],
        "accepted_values": [False, True, 0, 1]
    },
    "discharge_mrs": {
        "type": list,
        "default_value": [1, 2, 3, 4, 5, 6],
        "accepted_values": [1, 2, 3, 4, 5, 6]
    },
    "year_quarter": {
        "type": list,
        "default_value": ["2018 Q1", "2018 Q2", ..., "2022 Q4"],
        "accepted_values": ["2018 Q1", "2018 Q2", ..., "2022 Q4"]
    },
    "qi_error": {
        "type": bool,
        "default_value": False,
        "accepted_values": [False, True, 0, 1]
    },
    "qi_trend": {
        "type": bool,
        "default_value": False,
        "accepted_values": [False, True, 0, 1]
    },
    "compare_country": {
        "type": bool,
        "default_value": False,
        "accepted_values": [False, True, 0, 1]
    },
    "aggregation_type": {
        "type": str,
        "default_value": "median",
        "accepted_values": ["median", "mean", "standard derivation", "minimum", "maximum"]
    }
}
ACCEPTED_REGRESSION_TYPE = ["linear", "polynomial"]

ERROR_SELECTED_VALUE_NOT_ACCEPTED = f"Invalid selected value. Supported values are: {', '.join(ACCEPTED_SELECTED_VALUES.keys())}"
ERROR_COMPARISON_VALUE_NOT_ACCEPTED = f"Invalid comparison value. Supported values are:{', '.join(ACCEPTED_COMPARISON_VALUES)}"
ERROR_FILTER_VALUE_NOT_ACCEPTED = f"Invalid selected value. Supported filter are: {', '.join(ACCEPTED_FILTER_VALUES)}"
ERROR_UPDATE_FILTERS_NAME = f"Invalid filter name. Supported filters are: {', '.join(ACCEPTED_FILTER_VALUES.keys())}"
ERROR_UPDATE_VALUE_TYPE = f"Invalid filter value type."
ERROR_UPDATE_VALUE = "Invalid filter value."
ERROR_UPDATE_NAME_AND_VALUE = "You must provide one filter name and one filter value."
ERROR_REGRESSION_TYPE = f"Invalid regression type. Supported types are: {', '.join(ACCEPTED_REGRESSION_TYPE)}"