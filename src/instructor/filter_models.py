from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

from src.instructor.base_models import AliasEnum

# --- Numeric Filters ---


class ComparisonProperty(AliasEnum):
    GreaterOrEqual = ("GE", "greater than or equal", "at least", "no less than", "≥", "=>")
    LessOrEqual = ("LE", "less than or equal", "at most", "no more than", "≤", "<=")
    LessThan = ("LT", "less than", "fewer than", "<", "below")
    GreaterThan = ("GT", "greater than", "more than", ">", "above")
    Equal = ("EQ", "equal to", "equals", "==", "is")
    NotEqual = ("NE", "not equal to", "not equals", "!=", "is not")


class AgeFilter(BaseModel):
    type: Literal["AgeFilter"] = "AgeFilter"
    operator: ComparisonProperty = Field(
        ...,
        description=("Comparison operator for the patient's age. Use to filter patients by specific age thresholds or ranges. Accepts aliases like '>=', '<', or 'equal to'."),
        examples=[">=", "<=", "<", ">", "==", "!="],
    )
    value: int = Field(
        ...,
        description="The age value to compare against, in years.",
        examples=[50, 18, 65],
    )


class NIHSSFilter(BaseModel):
    type: Literal["NIHSSFilter"] = "NIHSSFilter"
    operator: ComparisonProperty = Field(
        ...,
        description=("Comparison operator for the patient's NIHSS score (National Institutes of Health Stroke Scale). Used to filter based on stroke severity. Accepts aliases like '>=', '<', or 'equal to'."),
        examples=[">=", "<=", "<", ">", "==", "!="],
    )
    value: int = Field(
        ...,
        description="NIHSS score to filter on. Higher scores indicate more severe stroke symptoms.",
        examples=[0, 4, 15, 21],
    )


# --- Enum Filters ---


class SexProperty(AliasEnum):
    Male = ("MALE", "man", "m")
    Female = ("FEMALE", "woman", "f")
    Other = ("OTHER", "non-binary", "genderqueer", "agender", "genderfluid")
    Unknown = ("UNKNOWN", "unspecified", "not provided", "n/a", "na")


class SexFilter(BaseModel):
    type: Literal["SexFilter"] = "SexFilter"
    value: SexProperty = Field(
        ...,
        description="The sex of the patient",
        examples=["MALE", "FEMALE", "OTHER", "UNKNOWN"],
    )


class StrokeProperty(AliasEnum):
    Ischemic = ("ISCHEMIC", "ischemic stroke", "clot stroke", "blockage stroke")
    IntracerebralHemorrhage = ("INTRACEREBRAL_HEMORRHAGE", "ich", "brain bleed", "intracerebral bleeding", "intraparenchymal hemorrhage")
    TransientIschemic = ("TRANSIENT_ISCHEMIC", "tia", "mini stroke", "transient ischemic attack")
    Subaracnoid = ("SUBARACHNOID_HEMORRHAGE", "sah", "aneurysm rupture", "subarachnoid bleed")
    CerebralVenousThrombosis = ("CEREBRAL_VENOUS_THROMBOSIS", "cvt", "venous stroke", "cerebral vein clot")
    StrokeMimics = ("STROKE_MIMICS", "mimics", "stroke-like symptoms", "not a real stroke", "conversion disorder")
    Undetermined = ("UNDETERMINED", "unknown stroke type", "unspecified", "unclear diagnosis")


class StrokeFilter(BaseModel):
    type: Literal["StrokeFilter"] = "StrokeFilter"
    value: StrokeProperty = Field(
        ...,
        description=("The stroke subtype to filter on. Valid values include ischemic stroke, hemorrhagic types, and mimics. Accepts aliases like 'TIA', 'brain bleed', or 'stroke mimic'."),
        examples=["ISCHEMIC", "TIA", "STROKE_MIMICS"],
    )


# --- Date Filter ---


class DateFilter(BaseModel):
    type: Literal["DateFilter"] = "DateFilter"
    operator: ComparisonProperty = Field(
        ...,
        description=("Comparison operator for date-based filtering. Use to filter records by a specific date or date range. Common operators include '>=', '<', or '=='."),
        examples=[">=", "<", "=="],
    )
    value: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date to filter on, in ISO format: YYYY-MM-DD",
        examples=["2023-01-01", "2024-06-15"],
        json_schema_extra={"format": "date"},
    )


class BooleanProperty(AliasEnum):
    Thrombectomy = ("THROMBECTOMY", "clot removal", "mechanical thrombectomy", "embolectomy")
    Thrombolysis = ("THROMBOLYSIS", "tpa", "alteplase", "clot-busting drug", "lysis treatment")
    Before_Onset_Cilostazol = ("BEFORE_ONSET_CILOSTAZOL", "cilostazol before onset")
    Before_Onset_Clopidogrel = ("BEFORE_ONSET_CLOPIDOGREL", "plavix", "clopidogrel before stroke")
    Before_Onset_Ticagrelor = ("BEFORE_ONSET_TICAGRELOR", "brilinta", "ticagrelor pre-stroke")
    Before_Onset_Ticlopidine = ("BEFORE_ONSET_TICLOPIDINE", "ticlopidine before stroke")
    Before_Onset_Prasugrel = ("BEFORE_ONSET_PRASUGREL", "prasugrel before stroke")
    Before_Onset_Dipyridamole = ("BEFORE_ONSET_DIPYRIDAMOLE", "dipyridamole pre-stroke")
    Before_Onset_Other_Antiplatelet = ("BEFORE_ONSET_OTHER_ANTIPLATELET", "other antiplatelet used", "unknown antiplatelet")
    Before_Onset_Any_Antiplatelet = ("BEFORE_ONSET_ANY_ANTIPLATELET", "on any antiplatelet", "antiplatelet therapy")
    Before_Onset_Warfarins = ("BEFORE_ONSET_WARFARINS", "warfarin", "coumadin")
    Before_Onset_Dabigatran = ("BEFORE_ONSET_DABIGATRAN", "pradaxa", "dabigatran before stroke")
    Before_Onset_Rivaroxaban = ("BEFORE_ONSET_RIVAROXABAN", "xarelto", "rivaroxaban pre-stroke")
    Before_Onset_Apixaban = ("BEFORE_ONSET_APIXABAN", "eliquis", "apixaban before stroke")
    Before_Onset_Edoxaban = ("BEFORE_ONSET_EDOXABAN", "lixiana", "edoxaban pre-stroke")
    Before_Onset_Other_Anticoagulant = ("BEFORE_ONSET_OTHER_ANTICOAGULANT", "other anticoagulant used", "unknown blood thinner")
    Before_Onset_Any_Anticoagulant = ("BEFORE_ONSET_ANY_ANTICOAGULANT", "on any anticoagulant", "any blood thinner")
    Before_Onset_Statin = ("BEFORE_ONSET_STATIN", "on statin", "statin before stroke", "lipid lowering")
    Before_Onset_Heparin = ("BEFORE_ONSET_HEPARIN", "on heparin", "heparin before stroke")
    Before_Onset_Contraception = ("BEFORE_ONSET_CONTRACEPTION", "on birth control", "hormonal contraception", "contraceptives before stroke")


class BooleanFilter(BaseModel):
    type: Literal["BooleanFilter"] = "BooleanFilter"
    property: BooleanProperty = Field(
        ...,
        description=(
            "A boolean clinical property indicating the presence or absence of a specific condition, "
            "medication, or treatment. For example, 'THROMBECTOMY' checks whether the patient received a "
            "mechanical clot removal procedure. All values are predefined in BooleanProperty. "
            "The field accepts natural phrases like 'clot removal', 'was on statin', or 'took aspirin before onset'."
        ),
        examples=["THROMBECTOMY", "BEFORE_ONSET_STATIN", "BEFORE_ONSET_CLOPIDOGREL"],
    )
    value: bool = Field(
        ...,
        description="Whether the selected boolean property is true or false for the patient.",
        examples=[True, False],
    )


# --- Logical Wrappers ---

FilterLeaf = Union[AgeFilter, NIHSSFilter, SexFilter, StrokeFilter, DateFilter, BooleanFilter]


class OperatorProperty(AliasEnum):
    AND = ("AND", "&", "&&")
    OR = ("OR", "|", "||")
    NOT = ("NOT", "!=", "=!", "!!")


class LogicalFilter(BaseModel):
    operator: OperatorProperty = Field(
        ...,
        description=("Logical operator to combine multiple filters. Use AND to require all conditions, OR to allow any condition, and NOT to exclude specific filters. Accepts symbols like '&&', '|', '!='."),
        examples=["AND", "OR", "NOT", "&&", "!=", "||"],
    )
    children: List[Union["LogicalFilter", FilterLeaf]] = Field(
        ...,
        description=("A list of nested filters or logical expressions. For AND/OR, provide two or more filters. For NOT, provide a single filter to be negated."),
        examples=[[{"age": {"operator": ">=", "value": 50}}, {"sex": {"value": "MALE"}}], [{"operator": "NOT", "children": [{"stroke": {"value": "UNDETERMINED"}}]}]],
    )


LogicalFilter.model_rebuild()


class FilterResponse(BaseModel):
    logicalFilter: Optional[LogicalFilter]

    # response: str | None
