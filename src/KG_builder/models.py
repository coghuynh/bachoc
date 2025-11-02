from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """Represents provenance and quality metadata for extracted knowledge graph elements"""
    source: str = Field(
        ..., 
        description="The exact verbatim sentence(s) from the source document from which this element was extracted. Must be complete sentences with full context. Include surrounding sentences if necessary for clarity. Preserve original punctuation, capitalization, and formatting exactly as it appears in the source."
    )


class LLMEntity(BaseModel):
    """Represents an entity extracted from text for knowledge graph construction"""
    name: str = Field(
        ..., 
        description="The canonical name or identifier of the entity. Should be normalized (e.g., 'John Smith' not 'john smith', 'Microsoft Corporation' not 'Microsoft Corp.'). Use the most complete form found in the text."
    )
    role: str = Field(
        ..., 
        description="The role of this entity in the triple relationship. Must be either 'subject' (the entity performing action or being described) or 'object' (the entity being acted upon or described). For example, in 'Apple acquired Beats', 'Apple' is subject and 'Beats' is object."
    )
    description: str = Field(
        ..., 
        description="A concise description of the entity based on context from the source text. Include key attributes, type information (person, organization, concept, etc.), and distinguishing characteristics. Should be 1-3 sentences that help disambiguate this entity from others with similar names."
    )
    metadata: Metadata = Field(
        ...,
        description="Provenance metadata tracking where and how this entity was extracted, confidence score, and exact text snippet. This metadata enables traceability, quality assessment, and citation back to original source material."
    )


class LLMPredicate(BaseModel):
    """Represents a predicate (relationship/property) extracted from text for knowledge graph triples"""
    name: str = Field(
        ..., 
        description="The normalized name of the predicate representing the relationship or property. Should be in verb form or property notation (e.g., 'acquired', 'founded_by', 'has_capital', 'is_CEO_of'). Use lowercase with underscores for multi-word predicates. Prefer active voice and consistent tense (present or past based on context)."
    )
    description: str = Field(
        ..., 
        description="A clear explanation of what this predicate represents, including the nature of the relationship it expresses between subject and object. Specify direction (e.g., 'indicates that subject acquired object' or 'connects person to their role'), temporal aspects if relevant, and any semantic nuances. Should be 1-2 sentences that enable proper interpretation of the triple."
    )
    metadata: Metadata = Field(
        ...,
        description="Provenance metadata documenting the extraction source, confidence level in the relationship interpretation, and the exact sentence where this relationship was stated or implied. Essential for validating relationship accuracy and understanding extraction context."
    )
 
    
class LLMTriple(BaseModel):
    """Represents a complete knowledge graph triple (subject-predicate-object) extracted from source text"""
    subject: LLMEntity = Field(
        ..., 
        description="The subject entity of this triple. This is the entity performing an action, possessing a property, or being described. The subject's 'role' field must be set to 'subject'. Example: In 'Apple acquired Beats', Apple is the subject entity."
    )
    predicate: LLMPredicate = Field(
        ..., 
        description="The predicate defining the relationship between subject and object. This captures the semantic connection, action, or property that links the two entities. Must accurately represent the relationship stated or implied in the source text."
    )
    object: LLMEntity = Field(
        ..., 
        description="The object entity of this triple. This is the entity receiving an action, being possessed as a property, or serving as the target of description. The object's 'role' field must be set to 'object'. Example: In 'Apple acquired Beats', Beats is the object entity."
    )
    metadata: Metadata = Field(
        ...,
        description="Provenance metadata for the entire triple relationship. Includes overall confidence in the triple extraction (considering both entities and predicate), and the exact source sentence expressing this relationship."
    )