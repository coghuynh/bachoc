from pydantic import BaseModel, Field
from typing import Optional

class Metadata(BaseModel):
    """Represents provenance and quality metadata for extracted knowledge graph elements"""
    source: str = Field(
        ...,
        description=(
            "The exact verbatim sentence(s) from the source document from which this element was extracted.\n"
        )
    )

    
class LLMTriple(BaseModel):
    """Represents a complete knowledge graph triple (subject-predicate-object) extracted from source text"""
    subject: str = Field(
        ..., 
        description="The subject entity of this triple. This is the entity performing an action, possessing a property, or being described. The subject's 'role' field must be set to 'subject'. Example: In 'Apple acquired Beats', Apple is the subject entity."
    )
    predicate: str = Field(
        ...,
        description="The predicate defining the relationship between subject and object. This captures the semantic connection, action, or property that links the two entities. Must accurately represent the relationship stated or implied in the source text."
    )
    object: str = Field(
        ..., 
        description="The object entity of this triple. This is the entity receiving an action, being possessed as a property, or serving as the target of description. The object's 'role' field must be set to 'object'. Example: In 'Apple acquired Beats', Beats is the object entity."
    )
    metadata: Optional[Metadata] = Field(
        default=None,
        description="Provenance metadata for the entire triple relationship. Includes overall confidence in the triple extraction (considering both entities and predicate), and the exact source sentence expressing this relationship."
    )
    
class TripleList(BaseModel):
    main_subject: str = Field(
        ...,
        description="The full name of the primary individual or entity being described throughout the document. This individual serves as the central subject for most personal and career-related triples."
    )
    triples: list[LLMTriple]