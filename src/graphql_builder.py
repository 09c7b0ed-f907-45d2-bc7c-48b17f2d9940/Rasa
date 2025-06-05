# graphql_builder.py
from abc import ABC, abstractmethod
from enum import Enum

from graphql_query import Argument, Field, Fragment, InlineFragment, Operation, Query

# -----------------------------
# Enums
# -----------------------------


class Operator(Enum):
    GreaterOrEqual = "GE"
    LessOrEqual = "LE"
    LessThan = "LT"
    GreaterThan = "GT"
    Equal = "EQ"
    NotEqual = "NE"


class EnumProperty(Enum):
    Stroke = "strokeType"
    Sex = "sexType"


class SexProperty(Enum):
    Male = "MALE"
    Female = "FEMALE"
    Other = "OTHER"
    Unknown = "UNKNOWN"


class StrokeProperty(Enum):
    Ischemic = "ISCHEMIC"
    IntracerebralHemorrhage = "INTRACEREBRAL_HEMORRHAGE"
    TransientIschemic = "TRANSIENT_ISCHEMIC"
    Subaracnoid = "SUBARACHNOID_HEMORRHAGE"
    CerebralVenousThrombosis = "CEREBRAL_VENOUS_THROMBOSIS"
    StrokeMimics = "STROKE_MIMICS"
    Undetermined = "UNDETERMINED"


class IntegerPropery(Enum):
    Age = "AGE"
    AdmissionNIHSS = "ADMISSION_NIHSS"


class BooleanProperty(Enum):
    Thrombectomy = "THROMBECTOMY"
    Thrombolysis = "THROMBOLYSIS"
    Before_Onset_Cilostazol = "BEFORE_ONSET_CILOSTAZOL"
    Before_Onset_Clopidogrel = "BEFORE_ONSET_CLOPIDOGREL"
    Before_Onset_Ticagrelor = "BEFORE_ONSET_TICAGRELOR"
    Before_Onset_Ticlopidine = "BEFORE_ONSET_TICLOPIDINE"
    Before_Onset_Prasugrel = "BEFORE_ONSET_PRASUGREL"
    Before_Onset_Dipyridamole = "BEFORE_ONSET_DIPYRIDAMOLE"
    Before_Onset_Other_Antiplatelet = "BEFORE_ONSET_OTHER_ANTIPLATELET"
    Before_Onset_Any_Antiplatelet = "BEFORE_ONSET_ANY_ANTIPLATELET"
    Before_Onset_Warfarins = "BEFORE_ONSET_WARFARINS"
    Before_Onset_Dabigatran = "BEFORE_ONSET_DABIGATRAN"
    Before_Onset_Rivaroxaban = "BEFORE_ONSET_RIVAROXABAN"
    Before_Onset_Apixaban = "BEFORE_ONSET_APIXABAN"
    Before_Onset_Edoxaban = "BEFORE_ONSET_EDOXABAN"
    Before_Onset_Other_Anticoagulant = "BEFORE_ONSET_OTHER_ANTICOAGULANT"
    Before_Onset_Any_Anticoagulant = "BEFORE_ONSET_ANY_ANTICOAGULANT"
    Before_Onset_Statin = "BEFORE_ONSET_STATIN"
    Before_Onset_Heparin = "BEFORE_ONSET_HEPARIN"
    Before_Onset_Contraception = "BEFORE_ONSET_CONTRACEPTION"


class DateProperty(Enum):
    DischargeDate = "DISCHARGE_DATE"


class Group(str, Enum):
    EMSPrenotification = "EMS_PRENOTIFICATION"
    FirstContactPlace = "FIRST_CONTACT_PLACE"
    IVTApplicationDepartment = "IVT_APPLICATION_DEPARTMENT"
    INRMode = "INR_MODE"


class Metric(str, Enum):
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
    Age = "AGE"
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
    AdmissionNihss = "ADMISSION_NIHSS"
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
    StrokeType = "STROKE_TYPE"
    StrokeMimicsDiagnosis = "STROKE_MIMICS_DIAGNOSIS"
    Thrombolysis = "THROMBOLYSIS"
    Thrombectomy = "THROMBECTOMY"
    ThrombolysisOnly = "THROMBOLYSIS_ONLY"
    ThrombolysisAndThrombectomy = "THROMBOLYSIS_AND_THROMBECTOMY"
    Recanalization = "RECANALIZATION"
    Dtn = "DTN"
    DtgPrimary = "DTG_PRIMARY"
    DtgSecondary = "DTG_SECONDARY"
    Dido = "DIDO"
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
    Dti = "DTI"
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


# -----------------------------
# Filter Builder
# -----------------------------


class BaseFilter(ABC):
    @abstractmethod
    def to_argument(self) -> Argument:
        pass


class FilterLeaf(BaseFilter):
    def __init__(self, filter_type: str, args: list[Argument]):
        self.filter_type = filter_type
        self.args = args

    def to_argument(self) -> Argument:
        return Argument(name="leaf", value=Argument(name=self.filter_type, value=self.args))


class LogicalNode(BaseFilter):
    def __init__(self, operator: str, *children: BaseFilter):
        self.operator = operator
        self.children = list(children)

    def to_argument(self) -> Argument:
        return Argument(name="node", value=[Argument(name="logicalOperator", value=self.operator), Argument(name="children", value=[[c.to_argument()] for c in self.children])])


def AND(*children: BaseFilter) -> LogicalNode:
    return LogicalNode("AND", *children)


def OR(*children: BaseFilter) -> LogicalNode:
    return LogicalNode("OR", *children)


def NOT(children: BaseFilter) -> LogicalNode:
    return LogicalNode("NOT", children)


def IntegerFilter(property: IntegerPropery, operator: Operator, value: int) -> FilterLeaf:
    return FilterLeaf(
        "integerCaseFilter",
        [
            Argument(name="property", value=property.value),
            Argument(name="operator", value=operator.value),
            Argument(name="value", value=value),
        ],
    )


def AgeFilter(operator: Operator, value: int) -> FilterLeaf:
    return IntegerFilter(IntegerPropery.Age, operator, value)


def NIHSSFilter(operator: Operator, value: int) -> FilterLeaf:
    return IntegerFilter(IntegerPropery.AdmissionNIHSS, operator, value)


def EnumFilter(Property: EnumProperty, value: str, contains: bool = True) -> FilterLeaf:
    return FilterLeaf(
        "enumCaseFilter",
        [
            Argument(
                name=Property.value,
                value=[
                    Argument(name="values", value=value),
                    Argument(name="contains", value=contains),
                ],
            )
        ],
    )


def SexFilter(property: SexProperty, contains: bool = True) -> FilterLeaf:
    return EnumFilter(EnumProperty.Sex, property.value, contains)


def StrokeFilter(property: StrokeProperty, contains: bool = True) -> FilterLeaf:
    return EnumFilter(EnumProperty.Stroke, property.value, contains)


def DateFilter(property: DateProperty, operator: Operator, value: str) -> FilterLeaf:
    return FilterLeaf(
        "dateCaseFilter",
        [
            Argument(name="property", value=property.value),
            Argument(name="operator", value=operator.value),
            Argument(name="value", value=f'"{value}"'),
        ],
    )


def DischargeDateFilter(operator: Operator, value: str) -> FilterLeaf:
    return DateFilter(DateProperty.DischargeDate, operator, value)


def BooleanFilter(property: BooleanProperty, value: bool = True) -> FilterLeaf:
    return FilterLeaf(
        "booleanCaseFilter",
        [
            Argument(name="property", value=property.value),
            Argument(name="value", value=value),
        ],
    )


# -----------------------------
# Metric Builder
# -----------------------------


class MetricBuilder:
    def __init__(self, metric_id: str, alias: str | None = None):
        self.metric_id = metric_id
        self.alias = alias or f"metric_{metric_id}"
        self.include_stats = False
        self.include_distribution = False
        self.bin_count = 24
        self.include_bounds = False
        self.lower = None
        self.upper = None
        self.include_group = False

    def with_bounds(self, lower: int, upper: int):
        self.include_bounds = True
        self.lower = lower
        self.upper = upper
        return self

    def with_distribution(self, bin_count: int, lower: int, upper: int):
        self.include_distribution = True
        self.bin_count = bin_count
        self.with_bounds(lower, upper)
        return self

    def with_stats(self):
        self.include_stats = True
        return self

    def with_group(self):
        self.include_group = True
        return self

    def to_field(self) -> Field:
        kpi_fields: list[str | Field | InlineFragment | Fragment] = ["caseCount"]
        if self.include_stats:
            kpi_fields += ["percents", "normalizedPercents", "cohortSize", "normalizedCohortSize", "median", "mean", "variance", "confidenceIntervalMean", "confidenceIntervalMedian", "interquartileRange", "quartiles"]
        if self.include_distribution:
            kpi_fields.append(Field(name="distribution", alias="d1", arguments=[Argument(name="binCount", value=self.bin_count)], fields=["edges", "caseCount", "percents", "normalizedPercents"]))

        kpiGroup_fields: list[str | Field | InlineFragment | Fragment] = [
            Field(
                name="kpi",
                alias="kpi1",
                arguments=[
                    Argument(
                        name="kpiOptions",
                        value=[
                            Argument(name="lowerBoundary", value=self.lower or 0),
                            Argument(name="upperBoundary", value=self.upper or 120),
                        ],
                    )
                ]
                if self.include_bounds
                else [],
                fields=kpi_fields,
            ),
        ]

        if self.include_group:
            kpiGroup_fields.append(Field(name="groupedBy", fields=["groupItemName"]))

        return Field(
            name="metric",
            alias=self.alias,
            arguments=[Argument(name="metricId", value=self.metric_id)],
            fields=[
                Field(
                    name="kpiGroup",
                    fields=kpiGroup_fields,
                ),
            ],
        )


# -----------------------------
# Query Builder
# -----------------------------


def build_query(metrics: list[MetricBuilder], caseFilters: BaseFilter | None = None, start_date: str = "1000-01-01", end_date: str = "9999-12-31", groupBy: Group | None = None, generalStats: bool = False, provider_group_id: int = 1) -> str:
    filter_Values = [
        Argument(
            name="timePeriod",
            value=[
                [
                    Argument(name="startDate", value=f'"{start_date}"'),
                    Argument(name="endDate", value=f'"{end_date}"'),
                ]
            ],
        ),
        Argument(name="dataOrigin", value=Argument(name="providerGroupId", value=[provider_group_id])),
    ]

    if caseFilters:
        filter_Values.append(Argument(name="caseFilter", value=caseFilters.to_argument()))

    getMetrics_Values = [
        Argument(
            name="filter",
            value=filter_Values,
        ),
    ]
    if groupBy:
        getMetrics_Values.append(Argument(name="groupBy", value=groupBy.value))
        for m in metrics:
            m.with_group()

    getMetrics_Fields: list[str | Field | InlineFragment | Fragment] = [*[m.to_field() for m in metrics]]

    if generalStats:
        getMetrics_Fields.append(
            Field(
                name="generalStatsGroup",
                fields=[
                    Field(
                        name="generalStatistics",
                        fields=["casesInPeriod", "filteredCasesInPeriod"],
                    )
                ],
            )
        )

    query = Query(
        name="getMetrics",
        arguments=getMetrics_Values,
        fields=getMetrics_Fields,
    )
    return Operation(type="query", queries=[query]).render()


# -----------------------------
# Main Demo
# -----------------------------

if __name__ == "__main__":
    filters = AND(
        DischargeDateFilter(Operator.GreaterThan, "2023-09-01"),
        DischargeDateFilter(Operator.LessThan, "2024-09-01"),
        NIHSSFilter(Operator.GreaterOrEqual, 2),
        OR(
            AND(
                SexFilter(SexProperty.Male),
                AgeFilter(Operator.GreaterOrEqual, 20),
                AgeFilter(Operator.LessOrEqual, 40),
            ),
            AND(
                SexFilter(SexProperty.Female),
                AgeFilter(Operator.GreaterOrEqual, 30),
                AgeFilter(Operator.LessOrEqual, 50),
            ),
        ),
        NOT(StrokeFilter(StrokeProperty.Undetermined)),
        NOT(BooleanFilter(BooleanProperty.Thrombectomy, False)),
    )

    metrics = [
        MetricBuilder(Metric.Age).with_distribution(bin_count=25, lower=25, upper=50),
        MetricBuilder(Metric.AdmissionNihss).with_stats(),
        MetricBuilder(Metric.Dtn).with_distribution(bin_count=1, lower=0, upper=120).with_stats(),
    ]

    queryComplex = build_query(metrics, filters, groupBy=Group.FirstContactPlace, generalStats=True)

    print(queryComplex)

    queryMinimal = build_query([MetricBuilder(Metric.Age)])

    # print(queryMinimal)
