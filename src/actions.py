from utils import plot_handler
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
from hvac import Client
import os
from dotenv import load_dotenv
from vault_client import VaultClient
from graphql_client import GraphQLClient

logger = logging.getLogger(__name__)
vault_client = VaultClient(os.getenv("VAULT_ADDRESS"), os.getenv("VAULT_TOKEN"))
graphql_client = GraphQLClient(os.getenv("GRAPHQL_URL"))

PLOT_HANDLER = plot_handler.PlotHandler()
ALLOWED_PLOT_TYPES = ["line", "bar", "pie", "barh"]
ALLOWED_SELECTED_VALUES = [
    "age",
    "gender",
    "hospital_stroke",
    "stroke_type",
    "nihss_score",
    "thrombolysis",
    "no_thrombolysis_reason",
    "door_to_needle",
    "door_to_imaging",
    "onset_to_door",
    "imaging_done",
    "imaging_type",
    "dysphagia_screening_type",
    "door_to_groin",
    "before_onset_antidiabetics",
    "before_onset_cilostazol",
    "before_onset_clopidrogel",
    "before_onset_ticagrelor",
    "before_onset_ticlopidine",
    "before_onset_prasugrel",
    "before_onset_dipyridamol",
    "before_onset_warfarin",
    "risk_hypertension",
    "risk_diabetes",
    "risk_hyperlipidemia",
    "risk_congestive_heart_failure",
    "risk_smoker",
    "risk_previous_ischemic_stroke",
    "risk_previous_hemorrhagic_stroke",
    "risk_coronary_artery_disease_or_myocardial_infarction",
    "risk_hiv",
    "bleeding_source",
    "discharge_mrs",
    "discharge_nihss_score",
    "three_m_mrs",
    "covid_test",
    "physiotherapy_start_within_3days",
    "occup_physiotherapy_received",
    "glucose",
    "cholesterol",
    "sys_blood_pressure",
    "dis_blood_pressure",
    "perfusion_core",
    "hypoperfusion_core",
    "stroke_mimics_diagnosis",
    "prestroke_mrs",
    "tici_score",
    "prenotification",
    "ich_score",
    "hunt_hess_score",
]

class ActionTestAPIs(Action):

    def name(self) -> Text:
        return "action_test_apis"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        try:
            token = vault_client.get_secret("tokens", tracker.sender_id)
            if token:
                dispatcher.utter_message(
                    text="Successfully retrieved token from Vault."
                )
            else:
                dispatcher.utter_message(
                    text="Unable to retrieve token from Vault."
                )
        except Exception as e:
            logger.error(f"Error retrieving token from Vault: {e}")
            dispatcher.utter_message(text="Error retrieving token from Vault.")

        query = """
query {
  getMetrics(
    filter: {
      timePeriod: [
        { startDate: "2022-01-01", endDate: "2022-12-31" }
      ],
      dataOrigin: { providerGroupId: [1] }
    }) {
    m1: metric(metricId: DTN) {
      labels
      kpiGroup {
        dataOrigin {
          providerGroupId
        }
        kpi {
          caseCount
        }
      }
    }
  }
}
        """
        
        try:
            response = graphql_client.query(query, token)
            if response:
                dispatcher.utter_message(text="Successfully able to query the GraphQL server.")
            else:
                dispatcher.utter_message(text="Unable to query the GraphQL server.")
        except Exception as e:
            logger.error(f"Error querying the GraphQL server: {e}")
            dispatcher.utter_message(text="Error querying the GraphQL server.")
        
        if token is not None and response is None:
            dispatcher.utter_message(text="Token might be expired.")
        if token is None and response is not None:
            dispatcher.utter_message(text="How?")

        return []


class ActionChangePlottype(Action):

    def name(self) -> Text:
        return "action_change_plottype"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        plot_type = tracker.get_slot("plot_type")

        if plot_type:
            if plot_type.lower() not in ALLOWED_PLOT_TYPES:
                dispatcher.utter_message(
                    text=f"Sorry, I don't understand. Can you try rephrasing?"
                )
                return {"plot_type": None}

        PLOT_HANDLER.change_arg("type", plot_type)
        args = PLOT_HANDLER.send_args()

        dispatcher.utter_message(json_message={"args": args})
        logger.info({"args": args})
        return []


class ActionChangeSelectedvalue(Action):

    def name(self) -> Text:
        return "action_change_selectedvalue"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        selected_value = tracker.get_slot("selected_value")

        if selected_value:
            if selected_value.lower() not in ALLOWED_SELECTED_VALUES:
                dispatcher.utter_message(
                    text=f"Sorry, I don't understand. Can you try rephrasing?"
                )
                return {"selected_value": None}
            dispatcher.utter_message(text=f"OK! I will create a {selected_value} plot.")

        PLOT_HANDLER.change_arg("variable", selected_value)
        data = PLOT_HANDLER.edit_data(tracker.get_slot("nat_value"))

        dispatcher.utter_message(json_message={"data": data})
        logger.info({"data": data})
        return []


class ActionToggleNationalValue(Action):

    def name(self) -> Text:
        return "action_toggle_national_value"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Get the current value and ensure it's a proper boolean
        current_value = tracker.get_slot("nat_value")

        # Log the raw current value and its type for debugging
        logger.info(f"Raw current value: {current_value}")
        logger.info(f"Type of current value: {type(current_value)}")

        # Convert to boolean if it's a string
        if isinstance(current_value, str):
            current_value = current_value.lower() == "true"

        # Toggle the boolean value
        new_value = not current_value

        # Log values to debug the toggle process
        logger.info(f"Toggling National Value")
        logger.info(f"Current value: {current_value}")
        logger.info(f"New value: {new_value}")

        # Update plot handler
        PLOT_HANDLER.change_arg("show_nat_val", new_value)
        args = PLOT_HANDLER.send_args()
        data = PLOT_HANDLER.edit_data(new_value)

        # Send the response message
        dispatcher.utter_message(
            text="We are {} the national value.".format(
                "showing" if new_value else "hiding"
            )
        )
        dispatcher.utter_message(json_message={"data": data, "args": args})

        # Log the updated data and arguments
        logger.info({"data": data, "args": args})

        # Return the updated slot with the new value
        return [SlotSet("nat_value", new_value)]


class PrefillSlots(Action):
    def name(self) -> Text:
        return "action_prefill_slots"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        plot_type = "line"
        nat_value = False
        selected_value = "door_to_needle"
        real_diff = False

        return [
            SlotSet("plot_type", plot_type),
            SlotSet("nat_value", nat_value),
            SlotSet("selected_value", selected_value),
            SlotSet("real_diff", real_diff),
        ]


class ActionInitialise(Action):
    def name(self) -> Text:
        return "action_initialise"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        selected_value = tracker.get_slot("selected_value")
        nat_value = tracker.get_slot("nat_value")
        plot_type = tracker.get_slot("plot_type")

        PLOT_HANDLER.change_arg("type", plot_type)
        PLOT_HANDLER.change_arg("show_nat_val", nat_value)
        PLOT_HANDLER.change_arg("variable", selected_value)
        args = PLOT_HANDLER.send_args()
        data = PLOT_HANDLER.edit_data(nat_value)

        dispatcher.utter_message(json_message={"data": data, "args": args})
        logger.info({"data": data, "args": args})
        return []


# 2024-07-23 09:44:05 ERROR    rasa_sdk.endpoint  - Exception occurred during execution of request <Request: POST /webhook>
# File "/app/actions/actions.py", line 143, in run
#  p_value, cohens_d, no_2022_q2_data = PLOT_HANDLER.compare_to_past()
# File "/app/actions/utils/plot_handler.py", line 113, in compare_to_past
#  mean_diff = q2_data.mean() - q1_data.mean()
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/series.py", line 6549, in mean
#  return NDFrame.mean(self, axis, skipna, numeric_only, **kwargs)
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/generic.py", line 12420, in mean
#  return self._stat_function(
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/generic.py", line 12377, in _stat_function
#  return self._reduce(
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/series.py", line 6457, in _reduce
#  return op(delegate, skipna=skipna, **kwds)
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/nanops.py", line 147, in f
#  result = alt(values, axis=axis, skipna=skipna, **kwds)
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/nanops.py", line 404, in new_func
#  result = func(values, axis=axis, skipna=skipna, mask=mask, **kwargs)
# File "/opt/venv/lib/python3.10/site-packages/pandas/core/nanops.py", line 719, in nanmean
#  the_sum = values.sum(axis, dtype=dtype_sum)
# File "/opt/venv/lib/python3.10/site-packages/numpy/core/_methods.py", line 48, in _sum
#  return umr_sum(a, axis, dtype, out, keepdims, initial, where)
# TypeError: unsupported operand type(s) for +: 'int' and 'str'


class ActionVariableTTest(Action):
    def name(self) -> Text:
        return "action_variable_ttest"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        p_value, cohens_d, no_2022_q2_data = PLOT_HANDLER.compare_to_past()

        if no_2022_q2_data:
            message = f"There was no data available for 2022 Q2. Comparing 2022 Q1 to 2021 Q4, the p-value of the wilcoxon test is {p_value:.4f}, Cohen's d is {cohens_d:.4f}."
        else:
            message = f"Comparing 2022 Q2 to 2022 Q1, the p-value of the wilcoxon test is {p_value:.4f}, Cohen's d is {cohens_d:.4f}."

        dispatcher.utter_message(text=message)

        if p_value < 0.1:
            dispatcher.utter_message(
                text=f"The p-value tells us that there is a {round(100 - (p_value * 100), 2)} difference between quarters, which means the difference is likely real."
            )
            dispatcher.utter_message(
                "Shall I use my A.I. abilities to find some possible causes for this difference? Or would you rather analyse the impact of this change on patient outcomes?"
            )
            real_diff = True
        else:
            dispatcher.utter_message(
                text=f"The p-value tells us that there is a {round(100 - (p_value * 100), 2)} difference between quarters, which means the difference is likely cause by random chance and variance."
            )
            dispatcher.utter_message("What variable would you like to explore next?")
            real_diff = False

        return [SlotSet("real_diff", real_diff)]


class ActionFindPredictors(Action):

    def name(self) -> Text:
        return "action_find_predictors"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        error, feature_weights = PLOT_HANDLER.find_predictors(True)

        if error:
            dispatcher.utter_message(f"Error occurred: {error}")
        else:
            mean_error = round(feature_weights["Root Mean Squared Error"], 2)
            rounded_feature_weights = {
                feat: round(weight, 2)
                for feat, weight in feature_weights["Shap Values"].items()
            }

            selected_value = tracker.get_slot("selected_value")
            dispatcher.utter_message(
                f"I built a separate model to predict {selected_value} based only on data from your hospital."
            )
            dispatcher.utter_message(f"The most important factors are:")
            features_str = ", ".join(rounded_feature_weights.keys())

            dispatcher.utter_message(features_str)
            dispatcher.utter_message(
                f"Would you rather: explore how {selected_value} affects your patients or do you want to explore one of the variables I have listed?"
            )

        return []


class ActionFindPredictorsGlobal(Action):

    def name(self) -> Text:
        return "action_global_predictions"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        error, feature_weights = PLOT_HANDLER.find_predictors(False)

        if error:
            dispatcher.utter_message(f"Error occurred: {error}")
        else:
            mean_error = round(feature_weights["Root Mean Squared Error"], 2)
            rounded_feature_weights = {
                feat: round(weight, 2)
                for feat, weight in feature_weights["Shap Values"].items()
            }

            selected_value = tracker.get_slot("selected_value")
            dispatcher.utter_message(
                f"I used the data I have from multiple hospitals including yours to build a regression model that predicts {selected_value}."
            )
            dispatcher.utter_message(
                f"Based on my model, here are the indicators which influence {selected_value} the most, in order of largest to smallest influence:"
            )
            features_str = ", ".join(rounded_feature_weights.keys())

            dispatcher.utter_message(features_str)

        return []


class ActionExploreEffects(Action):

    def name(self) -> Text:
        return "action_explore_effects"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        selected_value = "discharge_mrs"
        PLOT_HANDLER.change_arg("variable", selected_value)
        args = PLOT_HANDLER.send_args()
        data = PLOT_HANDLER.edit_data(False)

        dispatcher.utter_message(json_message={"data": data, "args": args})
        logger.info({"data": data, "args": args})
        return [SlotSet("selected_value", selected_value)]


class ActionDNTGuideline(Action):
    def name(self) -> Text:
        return "action_dnt_guideline"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        response = PLOT_HANDLER.DNT_guideline()
        dispatcher.utter_message(
            "The first guideline is that 75% of patients must be treated within 45 minutes."
        )
        dispatcher.utter_message(
            "It looks like your hospital does meet the guideline for DNT. Should I continue checking more guidelines?"
        )
        dispatcher.utter_message(
            "The next one is about screening at least 90% of patients for dysphagia."
        )

        return []


class ActionDysphagiaGuideline(Action):
    def name(self) -> Text:
        return "action_dysphagia_guideline"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        response = PLOT_HANDLER.dysphagia_guideline()

        dispatcher.utter_message(
            "While your hospital does screen many patients, you still do not meet the guideline on average. However, you did meet it for the most current quarter."
        )
        dispatcher.utter_message(
            "Should we check the last guideline? It's about 90% of eligible patients getting anticoagulants."
        )

        return []


class ActionAnticoagsGuideline(Action):
    def name(self) -> Text:
        return "action_anticoag_guideline"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        response = PLOT_HANDLER.guideline_anticoags()

        dispatcher.utter_message(
            "Again, your hospital provides the correct medication to many patients but does not meet the guideline of 90% except for the most recent quarter."
        )
        dispatcher.utter_message(
            "This is the last of the guidelines, let me know if you would like to explore something else."
        )

        return []


class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Set a slot to indicate fallback without sending a message
        return [SlotSet("fallback_triggered", True)]


class ActionAdmin(Action):

    def name(self) -> Text:
        return "action_admin"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List:

        # Log tracker attributes
        logger.info(f"Sender ID: {tracker.sender_id}")
        logger.info(f"Slots: {tracker.slots}")
        logger.info(f"Latest Message: {tracker.latest_message}")
        logger.info(f"Events: {tracker.events}")
        logger.info(f"Active Loop: {tracker.active_loop}")
        logger.info(f"Latest Action Name: {tracker.latest_action_name}")

        # Send a response message
        dispatcher.utter_message(text="ActionAdmin has been triggered!")

        # Return an empty list to signify no modification to the conversation state
        return []
