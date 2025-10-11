import pandas as pd


def default_schema():
    ENTITIES = {
        "Types": [
            "PERSON", "ORGANIZATION", "DATE", "TEXT",
            "GENDER_TYPE", "OCCUPATION", "PLACE", "COUNTRY", "UNIVERSITY"
        ],
        "Definitions": [
            "An individual human being identifiable by name or attributes.",
            "A structured group of people or institution such as a company or NGO.",
            "A specific point or period in time expressed in date format.",
            "Generic text or phrase that carries unstructured semantic meaning.",
            "Classification of a person’s gender such as Male, Female, or Other.",
            "A person’s job, profession, or role within an organization.",
            "A geographic area, location, or named place.",
            "A recognized nation or state with a defined territory and government.",
            "An academic institution providing higher education and research."
        ]
    }

    RELATIONSHIP = {
        "Types": [
            "worksAt", "bornIn", "studiedAt", "livesIn",
            "hasGender", "hasOccupation", "foundedBy", "locatedIn", "memberOf"
        ],
        "Definitions": [
            "Indicates the organization or company where a person works.",
            "Specifies the place or country where a person was born.",
            "Denotes the university or institution where a person studied.",
            "Specifies the location or city where a person currently lives.",
            "Defines the gender associated with a person entity.",
            "Links a person to their occupation or professional role.",
            "Indicates that an organization or institution was founded by a person.",
            "Relates a place or organization to a larger geographic entity.",
            "Represents membership of a person within a group or organization."
        ]
    }

    entity_df = pd.DataFrame({
        "Type": ENTITIES["Types"],
        "Definition": ENTITIES["Definitions"]
    })

    # Create relationship DataFrame
    relation_df = pd.DataFrame({
        "Type": RELATIONSHIP["Types"],
        "Definition": RELATIONSHIP["Definitions"]
    })

    entity_df.to_csv("./entities.csv", index=False, encoding="utf-8")
    relation_df.to_csv("relationships.csv", index=False, encoding="utf-8")
    


if __name__ == "__main__":
    default_schema()