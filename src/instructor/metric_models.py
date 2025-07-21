from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from src.instructor.base_models import AliasEnum


class KPI(AliasEnum):
    AaDtnLe60 = "AA_DTN_LE60"
    AaDtnLe45 = "AA_DTN_LE45"
    AaDtgLe120 = "AA_DTG_LE120"
    AaDtgLe90 = "AA_DTG_LE90"
    AaRecanalization = "AA_RECANALIZATION"
    AaImaging = "AA_IMAGING"
    AaSwallowingScreening = "AA_SWALLOWING_SCREENING"
    AaAnticoagulants = "AA_ANTICOAGULANTS"
    AaAntithrombotics = "AA_ANTITHROMBOTICS"
    AaStrokeUnit = "AA_STROKE_UNIT"
    Age = ("AGE", "patient age", "years", "age of patient")
    WakeupStroke = "WAKEUP_STROKE"
    InhospitalStroke = "INHOSPITAL_STROKE"
    ArrivalMode = "ARRIVAL_MODE"
    EmsPrenotification = "EMS_PRENOTIFICATION"
    AdmissionDepartment = "ADMISSION_DEPARTMENT"
    FirstContactPlace = "FIRST_CONTACT_PLACE"
    HospitalizedIn = "HOSPITALIZED_IN"
    Sex = "SEX"
    RiskFactorsType = "RISK_FACTORS_TYPE"
    BeforeOnsetMedication = "BEFORE_ONSET_MEDICATION"
    BeforeOnsetMedicationAisTia = "BEFORE_ONSET_MEDICATION_AIS_TIA"
    BeforeOnsetMedicationIch = "BEFORE_ONSET_MEDICATION_ICH"
    BeforeOnsetAntiplateletType = "BEFORE_ONSET_ANTIPLATELET_TYPE"
    BeforeOnsetAnticoagulantType = "BEFORE_ONSET_ANTICOAGULANT_TYPE"
    AdmissionNihss = ("ADMISSION_NIHSS", "stroke severity", "nihss", "initial nihss", "admission score")
    PrestrokeMrs = "PRESTROKE_MRS"
    Glucose = "GLUCOSE"
    Cholesterol = "CHOLESTEROL"
    SystolicPressure = "SYSTOLIC_PRESSURE"
    DiastolicPressure = "DIASTOLIC_PRESSURE"
    InrMode = "INR_MODE"
    ImagingDone = "IMAGING_DONE"
    ImagingType = "IMAGING_TYPE"
    OcclusionFound = "OCCLUSION_FOUND"
    OcclusionSite = "OCCLUSION_SITE"
    OldInfarctsSeen = "OLD_INFARCTS_SEEN"
    OldInfarctsType = "OLD_INFARCTS_TYPE"
    PerfusionDeficitType = "PERFUSION_DEFICIT_TYPE"
    PerfusionCore = "PERFUSION_CORE"
    Hypoperfusion = "HYPOPERFUSION"
    StrokeType = ("stroke subtype", "type of stroke", "stroke classification")
    StrokeMimicsDiagnosis = "STROKE_MIMICS_DIAGNOSIS"
    Thrombolysis = "THROMBOLYSIS"
    Thrombectomy = "THROMBECTOMY"
    ThrombolysisOnly = "THROMBOLYSIS_ONLY"
    ThrombolysisAndThrombectomy = "THROMBOLYSIS_AND_THROMBECTOMY"
    Recanalization = "RECANALIZATION"
    Dtn = ("DTN", "door to needle", "door to needle time", "time to thrombolysis", "time until thrombolytic treatment", "time to iv tpa", "time to treatment", "treatment delay")
    DtgPrimary = "DTG_PRIMARY"
    DtgSecondary = "DTG_SECONDARY"
    Dido = ("DIDO", "door in door out", "transfer delay", "time before transfer", "time spent before transfer", "time at initial hospital", "duration at referring hospital", "initial hospital stay time", "primary site delay", "door-to-door time")
    DoorToReperfusion = "DOOR_TO_REPERFUSION"
    MticiScore = "MTICI_SCORE"
    NoThrombolysisReason = "NO_THROMBOLYSIS_REASON"
    NoThrombectomyReason = "NO_THROMBECTOMY_REASON"
    MtComplicationsType = "MT_COMPLICATIONS_TYPE"
    MtComplications = "MT_COMPLICATIONS"
    ThrombolysisDrugs = "THROMBOLYSIS_DRUGS"
    ThrombolysisDrugDose = "THROMBOLYSIS_DRUG_DOSE"
    ThrombolysisApplicationDepartment = "THROMBOLYSIS_APPLICATION_DEPARTMENT"
    PostRecanalizationFindings = "POST_RECANALIZATION_FINDINGS"
    PostRecanalizationFindingType = "POST_RECANALIZATION_FINDING_TYPE"
    HemorrhagicTransformation = "HEMORRHAGIC_TRANSFORMATION"
    TiaClinicalSymptoms = "TIA_CLINICAL_SYMPTOMS"
    TiaSymptomsDuration = "TIA_SYMPTOMS_DURATION"
    BleedingSourceFound = "BLEEDING_SOURCE_FOUND"
    IchBleedingVolume = "ICH_BLEEDING_VOLUME"
    IchScore = "ICH_SCORE"
    IchTreatment = "ICH_TREATMENT"
    IchTreatmentType = "ICH_TREATMENT_TYPE"
    IchTreatmentTypeExtended = "ICH_TREATMENT_TYPE_EXTENDED"
    BleedingReasonFound = "BLEEDING_REASON_FOUND"
    BleedingReasonType = "BLEEDING_REASON_TYPE"
    BleedingAntidoteToAnticoagulants = "BLEEDING_ANTIDOTE_TO_ANTICOAGULANTS"
    AnticoagulantReversal = "ANTICOAGULANT_REVERSAL"
    AnticoagulantReversalGiven = "ANTICOAGULANT_REVERSAL_GIVEN"
    IntraventicularHemorrhage = "INTRAVENTICULAR_HEMORRHAGE"
    InfratentorialHemorrhage = "INFRATENTORIAL_HEMORRHAGE"
    SahTreatment = "SAH_TREATMENT"
    SahTreatmentType = "SAH_TREATMENT_TYPE"
    Nimodipine = "NIMODIPINE"
    HuntHessScore = "HUNT_HESS_SCORE"
    CvtTreatment = "CVT_TREATMENT"
    CvtTreatmentType = "CVT_TREATMENT_TYPE"
    PostAcuteCare = "POST_ACUTE_CARE"
    Craniectomy = "CRANIECTOMY"
    CraniectomyAgeGt60 = "CRANIECTOMY_AGE_GT60"
    CarotidArteriesImaging = "CAROTID_ARTERIES_IMAGING"
    CarotidStenosis = "CAROTID_STENOSIS"
    CarotidStenosisLevel = "CAROTID_STENOSIS_LEVEL"
    CarotidEndarterectomy = "CAROTID_ENDARTERECTOMY"
    CarotidEndarterectomyStenosisGt70 = "CAROTID_ENDARTERECTOMY_STENOSIS_GT70"
    AtrialFibrilationFlutter = "ATRIAL_FIBRILATION_FLUTTER"
    StrokeEtiologyKnownAis = "STROKE_ETIOLOGY_KNOWN_AIS"
    StrokeEtiologyTypeAis = "STROKE_ETIOLOGY_TYPE_AIS"
    StrokeEtiologyKnownAisTia = "STROKE_ETIOLOGY_KNOWN_AIS_TIA"
    StrokeEtiologyTypeAisTia = "STROKE_ETIOLOGY_TYPE_AIS_TIA"
    VteInterventionAis = "VTE_INTERVENTION_AIS"
    VteInterventionIch = "VTE_INTERVENTION_ICH"
    VteInterventionTypeAis = "VTE_INTERVENTION_TYPE_AIS"
    VteInterventionTypeIch = "VTE_INTERVENTION_TYPE_ICH"
    PostStrokeComplications = "POST_STROKE_COMPLICATIONS"
    PostStrokeComplicationsType = "POST_STROKE_COMPLICATIONS_TYPE"
    Day_1TemperatureChecks = "DAY_1_TEMPERATURE_CHECKS"
    Day_2TemperatureChecks = "DAY_2_TEMPERATURE_CHECKS"
    Day_3TemperatureChecks = "DAY_3_TEMPERATURE_CHECKS"
    ParacetamolOnFever = "PARACETAMOL_ON_FEVER"
    Day_1HyperglycemiaChecks = "DAY_1_HYPERGLYCEMIA_CHECKS"
    Day_2HyperglycemiaChecks = "DAY_2_HYPERGLYCEMIA_CHECKS"
    Day_3HyperglycemiaChecks = "DAY_3_HYPERGLYCEMIA_CHECKS"
    InsulinOnHyperglycemia = "INSULIN_ON_HYPERGLYCEMIA"
    SwallowingScreening = "SWALLOWING_SCREENING"
    SwallowingScreeningType = "SWALLOWING_SCREENING_TYPE"
    SwallowingScreeningPerformer = "SWALLOWING_SCREENING_PERFORMER"
    Physiotherapy = "PHYSIOTHERAPY"
    OccupationalTherapy = "OCCUPATIONAL_THERAPY"
    SpeechTherapy = "SPEECH_THERAPY"
    DischargeDestination = "DISCHARGE_DESTINATION"
    DischargeMedications = "DISCHARGE_MEDICATIONS"
    DischargeAnticoagulantsAfib = "DISCHARGE_ANTICOAGULANTS_AFIB"
    DischargeAnticoagulantTypeAfib = "DISCHARGE_ANTICOAGULANT_TYPE_AFIB"
    DischargeAntiplateletsNoAfib = "DISCHARGE_ANTIPLATELETS_NO_AFIB"
    DischargeAntiplateletTypeNoAfib = "DISCHARGE_ANTIPLATELET_TYPE_NO_AFIB"
    DischargeMrs = "DISCHARGE_MRS"
    SmokingCessation = "SMOKING_CESSATION"
    StrokeManagementAppointment = "STROKE_MANAGEMENT_APPOINTMENT"
    ThreeMonthMrs = "THREE_MONTH_MRS"
    HospitalStay = "HOSPITAL_STAY"
    DischargeNihss = "DISCHARGE_NIHSS"
    Dti = ("DTI", "door to imaging", "time to scan", "time to CT", "door-to-imaging time", "time until imaging", "time to first imaging", "time to initial scan", "initial CT timing")
    OnsetToDoor = "ONSET_TO_DOOR"
    DoorToIvAntihypertensiveInitiation = "DOOR_TO_IV_ANTIHYPERTENSIVE_INITIATION"
    DoorToSysBpLt140 = "DOOR_TO_SYS_BP_LT140"
    IvAntihypertensiveToSysBpLt140 = "IV_ANTIHYPERTENSIVE_TO_SYS_BP_LT140"
    IvAntihypertensive = "IV_ANTIHYPERTENSIVE"
    AchievingSystolicPressureLt140 = "ACHIEVING_SYSTOLIC_PRESSURE_LT140"
    DoorToReversalInitiation = "DOOR_TO_REVERSAL_INITIATION"
    NoAnticoagulationReversalReason = "NO_ANTICOAGULATION_REVERSAL_REASON"
    NoIchTreatmentReason = "NO_ICH_TREATMENT_REASON"
    DoorToEvacuation = "DOOR_TO_EVACUATION"


class GroupProperty(AliasEnum):
    EMSPrenotification = ("EMS_PRENOTIFICATION", "ems prenotification", "ems notified", "emergency pre-alert", "ambulance notified")
    FirstContactPlace = ("FIRST_CONTACT_PLACE", "first contact place", "place of first contact", "initial point of contact", "first seen")
    IVTApplicationDepartment = ("IVT_APPLICATION_DEPARTMENT", "ivt department", "thrombolysis department", "tpa department", "treatment department")
    INRMode = ("INR_MODE", "inr measurement method", "coagulation mode", "how inr was measured", "inr method")


class Distribution(BaseModel):
    bin_count: int = Field(
        100,
        description="Number of bins for the distribution. Must be a positive integer. Default should be the upper value devided by 100 and floored",
        examples=[1, 5, 10],
    )
    lower: int = Field(
        ...,
        description="Lower bound of the distribution range. Must be a integer less than upper.",
        examples=[0, 10, 20],
    )
    upper: int = Field(
        ...,
        description="Upper bound of the distribution range. Must be a integer greater than lower.",
        examples=[100, 200, 300],
    )

    @model_validator(mode="after")
    def check_bounds(self) -> "Distribution":
        if self.lower >= self.upper:
            raise ValueError("Lower bound must be a integer less than upper bound")
        if self.bin_count <= 0:
            raise ValueError("Bin count must be a integer greater than 0 (e.g., 10 or 25)")
        return self


class Metric(BaseModel):
    kpi: KPI = Field(
        ...,
        description=(
            "The clinical metric or key performance indicator to analyze or visualize. "
            "This could be a numeric measure like 'AGE' or 'DTN' (door-to-needle time), or a categorical variable like 'SEX' or 'STROKE_TYPE'. "
            "Natural phrases such as 'time to treatment', 'patient age', or 'stroke severity score' are accepted via aliases. "
            "All valid options are defined in the Metric enum."
        ),
        examples=["AGE", "DTN", "ADMISSION_NIHSS", "STROKE_TYPE"],
    )

    stats: Optional[bool] = Field(
        False,
        description=("If true, includes descriptive statistics for the selected metric — such as min, max, mean, median, and interquartile range. Useful for understanding central tendency and spread in the data."),
        examples=[True, False],
    )

    distribution: Optional[Distribution] = Field(
        None,
        description=("Defines parameters for computing a histogram or similar distribution-based visualization. Useful when visualizing metrics like 'AGE' or 'DTN' over a defined range and number of bins."),
        examples=[{"bin_count": 10, "lower": 0, "upper": 120}],
    )


class MetricsCollection(BaseModel):
    metrics: List[Metric] = Field(
        ...,
        description="A list of metrics to compute or analyze.",
        examples=[
            [
                {
                    "metric": "AGE",
                    "stats": True,
                }
            ],
            [
                {
                    "metric": "DTN",
                    "distribution": {
                        "bin_count": 5,
                        "lower": 0,
                        "upper": 120,
                    },
                }
            ],
        ],
    )
    group_by: Optional[GroupProperty] = Field(
        None,
        description="Optional grouping of metrics by a categorical property.",
        examples=["FIRST_CONTACT_PLACE", "EMS_PRENOTIFICATION"],
    )


class MetricResponse(BaseModel):
    metricsCollection: Optional[MetricsCollection] = None

    # response: str | None
