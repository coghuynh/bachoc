import json
import os
import re
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False




try:
    from jsonschema import Draft202012Validator, validate  # optional
    _HAS_JSONSCHEMA = True
except Exception:
    _HAS_JSONSCHEMA = False

# ---- Public constants --------------------------------------------------------
DEFAULT_MODEL = "gpt-4o-mini"

# ---- Core schema (exactly what you built) -----------------------------------
def get_schema() -> Dict[str, Any]:
    """Return the JSON schema object used in response_format."""
    return {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "title": "AcademicProfile",
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "person": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "id": { "type": ["string", "null"] },
            "name": { "type": "string" },
            "gender": { "type": ["string", "null"], "enum": ["male", "female", None] },
            "date_of_birth": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
            "nationality": { "type": ["string", "null"] },
            "ethnicity": { "type": ["string", "null"] },
            "religion": { "type": ["string", "null"] },
            "is_party_member": { "type": ["boolean", "null"] },
            "citizenship_id": { "type": ["string", "null"] },
            "aliases": { "type": "array", "items": { "type": "string" }, "default": [] }
          },
          "required": ["name"]
        },
        "contacts": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "permanent_address": { "type": ["string", "null"] },
            "hometown": { "type": ["string", "null"] },
            "mailing_address": { "type": ["string", "null"] },
            "work_address": { "type": ["string", "null"] },
            "phone_mobile": { "type": ["string", "null"] },
            "phone_home": { "type": ["string", "null"] },
            "email": { "type": ["string", "null"], "format": "email" }
          }
        },
        "current_affiliation": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "institution_id": { "type": ["string", "null"] },
            "institution_name": { "type": ["string", "null"] },
            "faculty_or_department": { "type": ["string", "null"] },
            "unit": { "type": ["string", "null"] },
            "position": { "type": ["string", "null"] }
          }
        },
        "employment_history": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "from": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "to": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "position_title": { "type": ["string", "null"] },
              "unit": { "type": ["string", "null"] },
              "institution_name": { "type": ["string", "null"] },
              "institution_id": { "type": ["string", "null"] },
              "country": { "type": ["string", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "visiting_appointments": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "role": { "type": ["string", "null"] },
              "institution_name": { "type": ["string", "null"] },
              "institution_id": { "type": ["string", "null"] },
              "from": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "to": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "education": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "degree": { "type": "string", "enum": ["Bachelor", "Master", "PhD", "Other"] },
              "field": { "type": ["string", "null"] },
              "specialization": { "type": ["string", "null"] },
              "institution_name": { "type": ["string", "null"] },
              "institution_id": { "type": ["string", "null"] },
              "country": { "type": ["string", "null"] },
              "date_awarded": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["degree", "provenance"]
          },
          "default": []
        },
        "discipline": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "sector": { "type": ["string", "null"] },
            "field": { "type": ["string", "null"] },
            "subfield": { "type": ["string", "null"] }
          }
        },
        "application": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "dossier_code": { "type": ["string", "null"] },
            "rank_applied": { "type": ["string", "null"], "enum": ["Professor", "Associate Professor", None] },
            "host_institution": { "type": ["string", "null"] },
            "field_council": { "type": ["string", "null"] },
            "date_submitted": { "type": ["string", "null"], "pattern": r"^\d{4}-\d{2}-\d{2}$" },
            "lecturer_type": { "type": ["string", "null"], "enum": ["Full-time", "Adjunct", "Visiting", None] }
          }
        },
        "research_interests": { "type": "array", "items": { "type": "string" }, "default": [] },
        "supervision": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "phd_completed": { "type": ["integer", "null"] },
            "masters_completed": { "type": ["integer", "null"] },
            "details": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "candidate_name": { "type": ["string", "null"] },
                  "level": { "type": ["string", "null"], "enum": ["PhD", "Master", "CK2", "BSNT", "Other", None] },
                  "role": { "type": ["string", "null"], "enum": ["Main", "Co", "Unknown", None] },
                  "institution_name": { "type": ["string", "null"] },
                  "from": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
                  "to": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
                  "date_awarded": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2})?(-\d{2})?$" },
                  "provenance": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                      "doc_id": { "type": ["string", "null"] },
                      "page": { "type": ["integer", "null"] }
                    },
                    "required": ["doc_id", "page"]
                  }
                },
                "required": ["provenance"]
              },
              "default": []
            }
          }
        },
        "projects": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "title": { "type": ["string", "null"] },
              "code": { "type": ["string", "null"] },
              "level": { "type": ["string", "null"], "enum": ["Institutional", "Ministerial", "National", "Other", None] },
              "role": { "type": ["string", "null"], "enum": ["PI", "Co-PI", "Secretary", "Other", None] },
              "from": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "to": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2}(-\d{2})?)?$" },
              "date_accepted": { "type": ["string", "null"], "pattern": r"^\d{4}(-\d{2})?(-\d{2})?$" },
              "result": { "type": ["string", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "publications": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "title": { "type": ["string", "null"] },
              "venue": { "type": ["string", "null"] },
              "issn_isbn": { "type": ["string", "null"] },
              "type": { "type": ["string", "null"], "enum": ["Journal", "Conference", "Book", "Chapter", "Other", None] },
              "indexing": { "type": ["string", "null"], "enum": ["SCI", "SCIE", "ESCI", "Scopus", "None", None] },
              "quartile": { "type": ["string", "null"], "enum": ["Q1", "Q2", "Q3", "Q4", None] },
              "impact_factor": { "type": ["number", "null"] },
              "year": { "type": ["string", "null"], "pattern": r"^\d{4}$" },
              "volume_issue_pages": { "type": ["string", "null"] },
              "is_lead_author": { "type": ["boolean", "null"] },
              "citations": { "type": ["number", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "books": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "title": { "type": ["string", "null"] },
              "type": { "type": ["string", "null"], "enum": ["Textbook", "Monograph", "Reference", "Guide", None] },
              "publisher": { "type": ["string", "null"] },
              "year": { "type": ["string", "null"], "pattern": r"^\d{4}$" },
              "is_reputable_publisher": { "type": ["boolean", "null"] },
              "chapter_pages": { "type": ["string", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "awards": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "name": { "type": ["string", "null"] },
              "issuer": { "type": ["string", "null"] },
              "year": { "type": ["string", "null"], "pattern": r"^\d{4}$" },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "discipline_actions": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "name": { "type": ["string", "null"] },
              "issuer": { "type": ["string", "null"] },
              "decision_no": { "type": ["string", "null"] },
              "effective_period": { "type": ["string", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "teaching_loads": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "academic_year": { "type": ["string", "null"], "pattern": r"^\d{4}-\d{4}$" },
              "hours_direct": { "type": ["number", "null"] },
              "hours_converted": { "type": ["number", "null"] },
              "hours_required": { "type": ["number", "null"] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "languages": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
              "language": { "type": ["string", "null"] },
              "level": { "type": ["string", "null"], "enum": ["Fluent", "Advanced", "Intermediate", "Basic", None] },
              "evidence": { "type": ["string", "null"], "enum": ["Degree abroad", "Certificate", "Taught in language", "Other", None] },
              "provenance": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                  "doc_id": { "type": ["string", "null"] },
                  "page": { "type": ["integer", "null"] }
                },
                "required": ["doc_id", "page"]
              }
            },
            "required": ["provenance"]
          },
          "default": []
        },
        "checkboxes": {
          "type": "object",
          "additionalProperties": False,
          "properties": {
            "is_giang_vien": { "type": ["boolean", "null"] },
            "is_giang_vien_thinh_giang": { "type": ["boolean", "null"] }
          }
        },
        "notes": { "type": ["string", "null"] }
      }
    }


def _ensure_required_fields(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure every object schema lists all of its properties in `required`.

    OpenAI's structured outputs currently mandate that when `strict=true` is
    used, each object must explicitly declare a `required` array that contains
    every property key. The schema we authored keeps many fields optional by
    allowing `null` or empty collections as values, so marking everything as
    required here simply forces the keys to be present while still permitting
    nulls. This function walks the schema recursively and amends any object
    definition that is missing (or partially specifying) its `required` list.
    """

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get("type")
            if node_type == "object" or (isinstance(node_type, list) and "object" in node_type):
                properties = node.get("properties")
                if isinstance(properties, dict):
                    required_keys = list(properties.keys())
                    if required_keys:
                        node["required"] = required_keys
                    for child in properties.values():
                        _walk(child)
            items = node.get("items")
            if isinstance(items, dict):
                _walk(items)
            elif isinstance(items, list):
                for child in items:
                    _walk(child)
            # Handle nested schemas that may appear under combinators like allOf/anyOf
            for key in ("allOf", "anyOf", "oneOf"):
                if key in node and isinstance(node[key], list):
                    for child in node[key]:
                        _walk(child)
        elif isinstance(node, list):
            for child in node:
                _walk(child)

    _walk(schema)
    return schema

def _system_prompt() -> str:
    return (
        "You are a data extraction agent. Output MUST conform to the provided JSON schema.\n\n"
        "Rules\n"
        "- Output only JSON (UTF-8, pretty).\n"
        "- Unknown scalars -> null; unknown arrays -> [].\n"
        "- Preserve Vietnamese diacritics in names/addresses.\n"
        "- Normalize dates to YYYY-MM-DD if exact, else YYYY-MM or YYYY, else null.\n"
        "- Normalize phones to digits only (keep leading zero).\n"
        "- Lowercase emails.\n"
        "- Infer gender: “Nam”→male, “Nữ”→female (if ambiguous -> null).\n"
        "- Interpret checkboxes “✓” as true, empty as false.\n"
        "- Do not fabricate data. Deduplicate repeated entries.\n"
        "- Add provenance objects to every array item (allow null doc_id/page if unknown).\n"
        "- Accept noisy punctuation/line breaks; treat section headers as delimiters.\n\n"
        "Constraints\n"
        "- Conform EXACTLY to the provided schema (keys, types, required fields)."
    )

# ---- Helpers ----------------------------------------------------------------
def _slugify(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    txt = text.strip().lower()
    txt = re.sub(r"[^\w\s-]", "", txt, flags=re.UNICODE)
    txt = re.sub(r"\s+", "-", txt)
    return txt

def _normalize_phone(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return digits or None

def _postprocess(data: Dict[str, Any]) -> Dict[str, Any]:
    # Phones and emails
    contacts = data.get("contacts") or {}
    for k in ("phone_mobile", "phone_home"):
        contacts[k] = _normalize_phone(contacts.get(k))
    if contacts.get("email"):
        contacts["email"] = contacts["email"].strip().lower()
    data["contacts"] = contacts

    # Fill missing institution_id from institution_name
    ca = data.get("current_affiliation") or {}
    if not ca.get("institution_id") and ca.get("institution_name"):
        ca["institution_id"] = f"inst:{_slugify(ca['institution_name'])}"
    data["current_affiliation"] = ca

    for key in ("employment_history", "education", "visiting_appointments"):
        arr = data.get(key) or []
        for item in arr:
            if not item.get("institution_id") and item.get("institution_name"):
                item["institution_id"] = f"inst:{_slugify(item['institution_name'])}"
        data[key] = arr
    return data

# ---- Public API --------------------------------------------------------------
def extract_academic_profile(
    text: str,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    validate_schema: bool = True
) -> Dict[str, Any]:
    """
    Extract an academic profile JSON from raw Vietnamese text using OpenAI's structured outputs.

    Args:
        text: raw input text (noisy forms, PDFs OCR text, etc.)
        api_key: OpenAI API key (falls back to env OPENAI_API_KEY if None)
        model: OpenAI model name
        validate_schema: if True and jsonschema is installed, validate the output

    Returns:
        dict matching the AcademicProfile schema
    """
    from openai import OpenAI  # local import to keep dependency optional for read-only use



    _api_key = api_key or os.getenv("OPEN_AI")
    if not _api_key:
        raise RuntimeError("OpenAI API key is required (pass api_key=... or set OPENAI_API_KEY).")

    client = OpenAI(api_key=_api_key)

    schema = _ensure_required_fields(get_schema())

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "academic_profile",
            "schema": schema,
            "strict": True
        }
    }

    system = _system_prompt()

    resp = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ],
        temperature=0
    )

    content = resp.choices[0].message.content
    data = json.loads(content)

    # Optional validation
    if validate_schema and _HAS_JSONSCHEMA:
        Draft202012Validator.check_schema(schema)
        validate(instance=data, schema=schema)

    # Post-process (phones/emails + institution IDs)
    data = _postprocess(data)
    return data

# ---- Simple CLI for quick tests ---------------------------------------------
if __name__ == "__main__":
    import sys
    src = sys.stdin.read()
    result = extract_academic_profile(src)
    print(json.dumps(result, ensure_ascii=False, indent=2))
