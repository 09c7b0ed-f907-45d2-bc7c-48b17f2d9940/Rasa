import base64
import datetime
import numpy as np
import json
import pandas as pd
import gzip
from scipy.stats import wilcoxon
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
import shap
import logging
import warnings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

class PlotHandler:
    def __init__(self, save_plot=False):
        self._date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._plot_name = None
        self._save = save_plot
        self.json_file_path = "utils/plot_args.json"
        self.json_data_path = "utils/data.json"
        self.data = pd.read_csv("utils/dataREanonymized_long.csv")

    def change_arg(self, arg, value):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)

        config['visualization'][arg] = value

        with open(self.json_file_path, 'w') as json_file:
            json.dump(config, json_file, indent=2)

    def send_args(self):
        with open(self.json_file_path, 'r') as file:
            json_data = json.load(file)

        compressed_content = gzip.compress(json.dumps(json_data).encode("utf-8"))
        compressed_content_decoded = base64.b64encode(compressed_content).decode("utf-8")

        payload = {"file_type": "args", "file_content": compressed_content_decoded}
        #logger.info(f"args sent by actions: {payload}")
        return payload

    def edit_data(self, show_nat_value):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)
        variable = config['visualization']['variable']

        filtered_dataframe = self.data[self.data['variable'].isin([variable])]

        if filtered_dataframe.empty:
            logger.error("Filtered DataFrame is empty!")
            raise ValueError("Filtered DataFrame is empty!")

        filtered_dataframe['Value'] = filtered_dataframe['Value'].astype(float).dropna()
        filtered_dataframe_site = filtered_dataframe[filtered_dataframe['site_id'].isin(["Vitality"])]

        if filtered_dataframe['ATTRIBUTE_TYPE'].iloc[0] in ['Quantitative', 'Categorical']:
            aggregated_dataframe = filtered_dataframe_site.groupby(['YQ', 'site_id'])['Value'].median().reset_index()
        else:
            aggregated_dataframe = filtered_dataframe_site.groupby(['YQ', 'site_id'])['Value'].mean().reset_index()

        if show_nat_value:
            filtered_dataframe_country = filtered_dataframe[~filtered_dataframe['site_id'].isin(["Vitality"])]
            if filtered_dataframe['ATTRIBUTE_TYPE'].iloc[0] in ['Quantitative', 'Categorical']:
                nat_df = filtered_dataframe_country.groupby(['YQ'])['Value'].median().reset_index()
            else:
                nat_df = filtered_dataframe_country.groupby(['YQ'])['Value'].mean().reset_index()
            nat_df = nat_df[['YQ', 'Value']]
            aggregated_dataframe = pd.merge(aggregated_dataframe, nat_df, on='YQ')
            aggregated_dataframe.rename(columns={'Value_y': 'nat_value', 'Value_x': 'Value'}, inplace=True)

        json_data = aggregated_dataframe.to_json(orient='records')

        with open(self.json_data_path, 'w') as json_file:
            json_file.write(json_data)

        with open(self.json_data_path, 'r') as json_file:
            config = json.load(json_file)

        compressed_content = gzip.compress(json.dumps(config).encode("utf-8"))
        compressed_content_decoded = base64.b64encode(compressed_content).decode("utf-8")

        payload = {"file_type": "data", "file_content": compressed_content_decoded}
        #logger.info(f"data sent by actions: {payload}")
        return payload

    def compare_to_past(self):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)
        var = config['visualization']['variable']

        variable_data = self.data[self.data['variable'] == var]
        variable_data['value'] = pd.to_numeric(variable_data['Value'], errors='coerce').dropna()

        if '2022 Q2' in variable_data['YQ'].values:
            q2_data = variable_data[variable_data['YQ'] == '2022 Q2']['Value']
            q1_data = variable_data[variable_data['YQ'] == '2022 Q1']['Value']
        else:
            q2_data = variable_data[variable_data['YQ'] == '2022 Q1']['Value']
            q1_data = variable_data[variable_data['YQ'] == '2021 Q4']['Value']

        min_len = min(len(q1_data), len(q2_data))
        q1_data = q1_data.sample(n=min_len, random_state=42) if len(q1_data) > len(q2_data) else q1_data
        q2_data = q2_data.sample(n=min_len, random_state=42) if len(q2_data) > len(q1_data) else q2_data

        _, p_value = wilcoxon(q2_data, q1_data)
        mean_diff = q2_data.mean() - q1_data.mean()
        pooled_std = np.sqrt((q1_data.var() + q2_data.var()) / 2)
        cohens_d = mean_diff / pooled_std
        no_2022_q2_data = '2022 Q2' not in variable_data['YQ'].values

        return p_value, cohens_d, no_2022_q2_data

    def find_predictors(self, local):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)

        data = self.data
        target_variable = config['visualization']['variable']
        predictor_variables = [var for var in data['variable'].unique() if var != target_variable]

        category_order = ['PC', 'Bleeding', 'Imaging', 'Treatment', 'PO', 'Discharge']
        category_positions = {category: index for index, category in enumerate(category_order)}
        target_category = data.loc[data['variable'] == target_variable, 'TAB'].iloc[0]

        if local:
            data = data[data['site_id'].isin(["Vitality"])]
        predictor_variables_filtered = [
            var for var in predictor_variables
            if category_positions[data.loc[data['variable'] == var, 'TAB'].iloc[0]] < category_positions[target_category]
        ]

        if target_category == 'PC':
            error = "The target variable is a patient characteristic, it cannot be predicted."
            return error, None

        data['Value'] = pd.to_numeric(data['Value'], errors='coerce')
        data_wide = data.pivot_table(index=['YQ', 'subject_id'], columns='variable', values='Value').reset_index().fillna(0)

        for var in data_wide.columns:
            if var not in predictor_variables_filtered and var != 'YQ':
                try:
                    data_wide[var] = pd.to_numeric(data_wide[var], errors='coerce')
                except KeyError:
                    logger.warning(f"Skipping variable {var} due to KeyError")

        filtered_indices = [i for i, var in enumerate(predictor_variables_filtered) if var in data_wide.columns]
        predictor_variables_filtered = [predictor_variables_filtered[i] for i in filtered_indices]
        predictor_variables_filtered_names = [data.loc[data['variable'] == var, 'INDICATOR'].iloc[0] for var in predictor_variables_filtered]

        X = data_wide[predictor_variables_filtered]
        y = data_wide[target_variable]

        gbr = GradientBoostingRegressor()
        gbr.fit(X, y)
        y_pred = gbr.predict(X)

        accuracy = mean_squared_error(y, y_pred, squared=False)
        feature_importances = gbr.feature_importances_

        sorted_indices = feature_importances.argsort()[::-1][:5]
        feature_weights = {predictor_variables_filtered[i]: feature_importances[i] for i in sorted_indices}

        explainer = shap.TreeExplainer(gbr)
        shap_values = explainer.shap_values(X)
        mean_shap_values = np.abs(shap_values).mean(axis=0)
        sorted_indices = np.argsort(mean_shap_values)[::-1][:10]
        shap_values = {predictor_variables_filtered_names[i]: mean_shap_values[i] for i in sorted_indices}

        return None, {'Root Mean Squared Error': accuracy, 'Feature Importances': feature_weights, 'Shap Values': shap_values}

    def DNT_guideline(self):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)

        data = self.data
        show_nat = config['visualization']['show_nat_val']
        df_filtered = data[data['site_id'].isin(["Vitality"])]

        filtered_df = df_filtered[df_filtered['variable'] == 'door_to_needle'].copy()
        filtered_df['Value'] = pd.to_numeric(filtered_df['Value'], errors='coerce').dropna()
        filtered_df['door_to_needle_below_60'] = filtered_df['Value'] < 45

        percentage_below_60 = filtered_df.groupby('YQ')['door_to_needle_below_60'].mean() * 100
        percentage_below_60_df = percentage_below_60.reset_index()
        percentage_below_60_df.columns = ['YQ', 'Value']

        if show_nat:
            df_filtered_nat = data[~data['site_id'].isin(["Vitality"])]
            filtered_df_nat = df_filtered_nat[df_filtered_nat['variable'] == 'door_to_needle'].copy()
            filtered_df_nat['Value'] = pd.to_numeric(filtered_df_nat['Value'], errors='coerce').dropna()
            filtered_df_nat['door_to_needle_below_60'] = filtered_df_nat['Value'] < 45
            percentage_below_60_nat = filtered_df_nat.groupby('YQ')['door_to_needle_below_60'].mean() * 100
            percentage_below_60_df_nat = percentage_below_60_nat.reset_index()
            percentage_below_60_df_nat.columns = ['YQ', 'Value']
            percentage_below_60_df['nat_value'] = percentage_below_60_df_nat['Value']

        json_data = percentage_below_60_df.to_json(orient='records')
        with open(self.json_data_path, 'w') as json_file:
            json_file.write(json_data)

        with open(self.json_data_path, 'r') as json_file:
            config = json.load(json_file)

        compressed_content = gzip.compress(json.dumps(config).encode("utf-8"))
        compressed_content_decoded = base64.b64encode(compressed_content).decode("utf-8")

        payload = {"file_type": "data", "file_content": compressed_content_decoded}
        #logger.info(f"data sent by actions: {payload}")
        return payload

    def dysphagia_guideline(self):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)

        data = self.data
        show_nat = config['visualization']['show_nat_val']
        df_filtered = data[data['site_id'].isin(["Vitality"])]

        filtered_df = df_filtered[df_filtered['variable'] == 'dysphagia_screening_type'].copy()
        non_null_counts = filtered_df.groupby('YQ')['Value'].count()
        total_patients = df_filtered.groupby('YQ')['subject_id'].nunique()
        percentage_filled_in = (non_null_counts / total_patients) * 100
        percentage_filled_in_df = percentage_filled_in.reset_index()
        percentage_filled_in_df.columns = ['YQ', 'Value']

        if show_nat:
            df_filtered_nat = data[~data['site_id'].isin(["Vitality"])]
            filtered_df_nat = df_filtered_nat[df_filtered_nat['variable'] == 'dysphagia_screening_type'].copy()
            non_null_counts_nat = filtered_df_nat.groupby('YQ')['Value'].count()
            total_patients_nat = df_filtered_nat.groupby('YQ')['subject_id'].nunique()
            percentage_filled_in_nat = (non_null_counts_nat / total_patients_nat) * 100
            percentage_filled_in_df_nat = percentage_filled_in_nat.reset_index()
            percentage_filled_in_df_nat.columns = ['YQ', 'Value']
            percentage_filled_in_df['nat_value'] = percentage_filled_in_df_nat['Value']

        json_data = percentage_filled_in_df.to_json(orient='records')
        with open(self.json_data_path, 'w') as json_file:
            json_file.write(json_data)

        with open(self.json_data_path, 'r') as json_file:
            config = json.load(json_file)

        compressed_content = gzip.compress(json.dumps(config).encode("utf-8"))
        compressed_content_decoded = base64.b64encode(compressed_content).decode("utf-8")

        payload = {"file_type": "data", "file_content": compressed_content_decoded}
        #logger.info(f"data sent by actions: {payload}")
        return payload

    def guideline_anticoags(self):
        with open(self.json_file_path, 'r') as json_file:
            config = json.load(json_file)

        data = self.data
        show_nat = config['visualization']['show_nat_val']
        df_filtered = data[data['site_id'].isin(["Vitality"])]

        filtered_df = df_filtered[df_filtered['variable'].isin([
            'discharge_warfarin', 'discharge_heparin', 'discharge_dabigatran',
            'discharge_rivaroxaban', 'discharge_apixaban', 'discharge_edoxaban',
            'discharge_cilostazol', 'discharge_clopidrogel', 'discharge_ticagrelor',
            'discharge_ticlopidine', 'discharge_prasugrel', 'discharge_dipyridamol'
        ])].copy()

        filtered_df['Value'] = pd.to_numeric(filtered_df['Value'], errors='coerce').fillna(0)
        filtered_df['any_discharge_medication'] = (filtered_df['Value'] == 1).astype(int)
        count_any_discharge_medication = filtered_df.groupby('YQ')['any_discharge_medication'].sum()
        total_patients = df_filtered.groupby('YQ')['subject_id'].nunique()
        percentage_any_discharge_medication = (count_any_discharge_medication / total_patients) * 100
        percentage_any_discharge_medication_df = percentage_any_discharge_medication.reset_index()
        percentage_any_discharge_medication_df.columns = ['YQ', 'Value']

        if show_nat:
            df_filtered_nat = data[~data['site_id'].isin(["Vitality"])]
            filtered_df_nat = df_filtered_nat[df_filtered_nat['variable'].isin([
                'discharge_warfarin', 'discharge_heparin', 'discharge_dabigatran',
                'discharge_rivaroxaban', 'discharge_apixaban', 'discharge_edoxaban',
                'discharge_cilostazol', 'discharge_clopidrogel', 'discharge_ticagrelor',
                'discharge_ticlopidine', 'discharge_prasugrel', 'discharge_dipyridamol'
            ])].copy()

            filtered_df_nat['Value'] = pd.to_numeric(filtered_df_nat['Value'], errors='coerce').fillna(0)
            filtered_df_nat['any_discharge_medication'] = (filtered_df_nat['Value'] == 1).astype(int)
            count_any_discharge_medication_nat = filtered_df_nat.groupby('YQ')['any_discharge_medication'].sum()
            total_patients_nat = df_filtered_nat.groupby('YQ')['subject_id'].nunique()
            percentage_any_discharge_medication_nat = (count_any_discharge_medication_nat / total_patients_nat) * 100
            percentage_any_discharge_medication_df_nat = percentage_any_discharge_medication_nat.reset_index()
            percentage_any_discharge_medication_df_nat.columns = ['YQ', 'Value']
            percentage_any_discharge_medication_df['nat_value'] = percentage_any_discharge_medication_df_nat['Value']

        json_data = percentage_any_discharge_medication_df.to_json(orient='records')
        with open(self.json_data_path, 'w') as json_file:
            json_file.write(json_data)

        with open(self.json_data_path, 'r') as json_file:
            config = json.load(json_file)

        compressed_content = gzip.compress(json.dumps(config).encode("utf-8"))
        compressed_content_decoded = base64.b64encode(compressed_content).decode("utf-8")

        payload = {"file_type": "data", "file_content": compressed_content_decoded}
        #logger.info(f"data sent by actions: {payload}")
        return payload
