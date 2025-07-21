from typing import Any, Dict, List, Text, Tuple, Optional
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
import logging

logger = logging.getLogger(__name__)

@DefaultV1Recipe.register(
    DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR, is_trainable=False
)
class EntityConsolidator(GraphComponent):
    """Consolidates duplicate entities extracted from the same message."""
    
    def __init__(self, config: Dict[Text, Any]) -> None:
        self._config = config
        # Configuration options with defaults
        self._position_matching = config.get("position_matching", "exact")  # "exact", "overlap", "ignore"
        self._overlap_threshold = config.get("overlap_threshold", 0.5)  # For overlap matching
        self._position_tolerance = config.get("position_tolerance", 0)  # Character tolerance for exact matching
        self._consolidation_key = config.get("consolidation_key", ["entity", "start", "end", "role", "value"])
        self._preserve_all_extractors = config.get("preserve_all_extractors", True)
        self._confidence_strategy = config.get("confidence_strategy", "highest")  # "highest", "average", "all"
        self._role_aware = config.get("role_aware", True)
        self._value_normalization = config.get("value_normalization", False)  # Normalize values before comparison
        self._debug_logging = config.get("debug_logging", False)
        self._collect_stats = config.get("collect_stats", False)
        self._stats = {"total_processed": 0, "total_consolidated": 0, "consolidation_ratio": 0.0}
        
        # Validate configuration
        if self._position_matching not in ["exact", "overlap", "ignore"]:
            raise ValueError(f"Invalid position_matching: {self._position_matching}")
        
        if not 0.0 <= self._overlap_threshold <= 1.0:
            raise ValueError(f"overlap_threshold must be between 0.0 and 1.0, got {self._overlap_threshold}")
        
        if self._position_tolerance < 0:
            raise ValueError(f"position_tolerance must be >= 0, got {self._position_tolerance}")
    
    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> "EntityConsolidator":
        return cls(config)

    def process(self, messages: List[Message]) -> List[Message]:
        for message in messages:
            entities = message.get("entities", [])
            if entities:
                if self._debug_logging:
                    logger.info(f"Before consolidation: {len(entities)} entities")
                    for i, ent in enumerate(entities):
                        logger.info(f"  {i}: {ent.get('entity')}={ent.get('value')} [{ent.get('start')}-{ent.get('end')}] role={ent.get('role')}")
                
                consolidated = self._consolidate_entities(entities)
                message.set("entities", consolidated)
                
                if self._debug_logging:
                    logger.info(f"After consolidation: {len(consolidated)} entities")
                    for i, ent in enumerate(consolidated):
                        logger.info(f"  {i}: {ent.get('entity')}={ent.get('value')} [{ent.get('start')}-{ent.get('end')}] role={ent.get('role')} extractors={len(ent.get('extractors', []))}")
        return messages

    def _normalize_value(self, value: Any) -> Any:
        """Normalize entity value if configured to do so."""
        if not self._value_normalization or not isinstance(value, str):
            return value
        return value.lower().strip()

    def _positions_match(self, ent1: Dict[str, Any], ent2: Dict[str, Any]) -> bool:
        """Check if two entities match based on position matching strategy."""
        if self._position_matching == "ignore":
            return True
        
        start1, end1 = ent1.get("start"), ent1.get("end")
        start2, end2 = ent2.get("start"), ent2.get("end")
        
        if start1 is None or end1 is None or start2 is None or end2 is None:
            return True  # Can't compare positions, assume match
        
        if self._position_matching == "exact":
            tolerance = self._position_tolerance
            return (abs(start1 - start2) <= tolerance and 
                   abs(end1 - end2) <= tolerance)
        
        elif self._position_matching == "overlap":
            # Calculate overlap ratio
            overlap_start = max(start1, start2)
            overlap_end = min(end1, end2)
            
            if overlap_start >= overlap_end:
                return False  # No overlap
            
            overlap_length = overlap_end - overlap_start
            min_length = min(end1 - start1, end2 - start2)
            
            if min_length == 0:
                return overlap_length > 0
            
            overlap_ratio = overlap_length / min_length
            return overlap_ratio >= self._overlap_threshold
        
        return False

    def _generate_key(self, ent: Dict[str, Any]) -> Tuple:
        """Generate consolidation key based on configuration."""
        key_parts = []
        
        for key_component in self._consolidation_key:
            if key_component == "entity":
                key_parts.append(ent.get("entity"))
            elif key_component == "value":
                value = ent.get("value")
                key_parts.append(self._normalize_value(value))
            elif key_component == "role":
                if self._role_aware:
                    key_parts.append(ent.get("role"))
            elif key_component == "start":
                if self._position_matching == "exact":
                    key_parts.append(ent.get("start"))
            elif key_component == "end":
                if self._position_matching == "exact":
                    key_parts.append(ent.get("end"))
            elif key_component == "position_range":
                # Custom key for position-based grouping
                start, end = ent.get("start"), ent.get("end")
                if start is not None and end is not None:
                    # Group by position ranges (useful for overlap matching)
                    range_key = f"{start//10}-{end//10}"  # Group by 10-char ranges
                    key_parts.append(range_key)
        
        return tuple(key_parts)

    def _consolidate_entities(self, entities: List[Dict[Text, Any]]) -> List[Dict[Text, Any]]:
        """Consolidate entities based on configuration."""
        original_count = len(entities)
        
        if self._position_matching in ["exact", "ignore"]:
            result = self._consolidate_by_key(entities)
        else:
            result = self._consolidate_by_overlap(entities)
        
        if self._collect_stats:
            self._stats["total_processed"] += original_count
            self._stats["total_consolidated"] += original_count - len(result)
            if self._stats["total_processed"] > 0:
                self._stats["consolidation_ratio"] = self._stats["total_consolidated"] / self._stats["total_processed"]
            
            if self._debug_logging:
                logger.info(f"Consolidation stats: {self._stats}")
        
        return result

    def _consolidate_by_key(self, entities: List[Dict[Text, Any]]) -> List[Dict[Text, Any]]:
        """Consolidate entities using key-based matching."""
        consolidated: Dict[Tuple, Dict[str, Any]] = {}
        
        for ent in entities:
            key = self._generate_key(ent)
            
            if key not in consolidated:
                consolidated[key] = self._create_consolidated_entity(ent)
            else:
                self._merge_entity_data(consolidated[key], ent)
        
        return list(consolidated.values())

    def _consolidate_by_overlap(self, entities: List[Dict[Text, Any]]) -> List[Dict[Text, Any]]:
        """Consolidate entities using overlap-based matching."""
        consolidated = []
        
        for ent in entities:
            merged = False
            
            for existing in consolidated:
                if (ent.get("entity") == existing.get("entity") and
                    (not self._role_aware or ent.get("role") == existing.get("role")) and
                    self._normalize_value(ent.get("value")) == self._normalize_value(existing.get("value")) and
                    self._positions_match(ent, existing)):
                    
                    self._merge_entity_data(existing, ent)
                    merged = True
                    break
            
            if not merged:
                consolidated.append(self._create_consolidated_entity(ent))
        
        return consolidated

    def _create_consolidated_entity(self, ent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new consolidated entity from the first occurrence."""
        consolidated = {
            "entity": ent.get("entity"),
            "start": ent.get("start"),
            "end": ent.get("end"),
            "value": ent.get("value"),
            "extractors": [],
            "role_extractors": [],
        }
        
        if self._role_aware and ent.get("role"):
            consolidated["role"] = ent.get("role")
        
        self._add_extractor_info(consolidated, ent)
        return consolidated

    def _merge_entity_data(self, consolidated: Dict[str, Any], ent: Dict[str, Any]) -> None:
        """Merge data from a new entity into an existing consolidated entity."""
        self._add_extractor_info(consolidated, ent)
        
        # Update position if needed (e.g., take the span that covers both)
        if self._position_matching == "overlap":
            start = min(consolidated.get("start", float('inf')), ent.get("start", float('inf')))
            end = max(consolidated.get("end", 0), ent.get("end", 0))
            if start != float('inf'):
                consolidated["start"] = start
            if end != 0:
                consolidated["end"] = end

    def _add_extractor_info(self, consolidated: Dict[str, Any], ent: Dict[str, Any]) -> None:
        """Add extractor information to consolidated entity."""
        if not self._preserve_all_extractors:
            return
        
        # Add entity extractor info
        extractor = ent.get("extractor")
        confidence = ent.get("confidence_entity") or ent.get("confidence")
        if extractor:
            extractor_info = {"extractor": extractor, "confidence": confidence}
            if extractor_info not in consolidated["extractors"]:
                consolidated["extractors"].append(extractor_info)
        
        # Add role extractor info
        role_extractor = ent.get("role_extractor")
        role_confidence = ent.get("confidence_role")
        if role_extractor:
            role_info = {"extractor": role_extractor, "confidence": role_confidence}
            if role_info not in consolidated["role_extractors"]:
                consolidated["role_extractors"].append(role_info)
        role_extractor = ent.get("role_extractor")
        role_confidence = ent.get("confidence_role")
        if role_extractor:
            role_info = {"extractor": role_extractor, "confidence": role_confidence}
            if role_info not in consolidated["role_extractors"]:
                consolidated["role_extractors"].append(role_info)
