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
            "học đại học tại", "học ngành", "công tác tại", "tọa lạc tại",
            "chuyên ngành", "thực tập tại", "nghiên cứu tại", "giữ chức vụ",
            "có địa chỉ", "có số điện thoại", "thỉnh giảng tại", "được cấp bằng",
            "được bổ nhiệm chức danh PGS vào", "đăng ký xét đạt tiêu chuẩn chức danh Phó Giáo Sư tại HĐGS cơ sở",
            "Đăng ký xét đạt tiêu chuẩn chức danh Phó Giáo Sư tại HĐGS ngành, liên ngành",
            "chủ yếu nghiên cứu", "đã hướng dẫn", "đã công bố", "đã hoàn thành", "là tác giả chính",
            "đã xuất bản", "đã được cấp", "đạt giải thưởng quốc gia quốc tế", "được khen thưởng"
        ],
        "Definitions": [
            "Indicates the university or institution where a person completed their undergraduate education.",
            "Specifies the academic discipline or field of study a person pursued during their education.",
            "Denotes the organization or institution where a person is or was employed.",
            "Indicates the geographical location or address of an entity (e.g., a university, an organization).",
            "Specifies the area of expertise or specialization within a broader field of study or work.",
            "Indicates the organization or institution where a person completed a formal internship.",
            "Denotes the institution or facility where a person conducted their research activities.",
            "Specifies the formal title or role a person occupied within an organization.",
            "Provides the physical mailing or street address of an person/entity.",
            "Provides the contact telephone number of an person/entity.",
            "Indicates the institution where a person gave lectures on a non-permanent or temporary basis.",
            "Specifies the degree or certification received by a person.",
            "Indicates the year or date when a person was formally given the academic title of Associate Professor.",
            "Indicates the local/institutional council where the person submitted their application for the Associate Professor title review.",
            "Indicates the national/specialized council where the person submitted their application for the Associate Professor title review.",
            "Specifies the main focus area or subject of a person's research activities.",
            "Indicates the number of theses, dissertations, or students a person successfully advised.",
            "Indicates the number of scientific articles, papers, or works a person has released.",
            "Indicates the number of research projects or tasks that have been finished.",
            "Specifies the number of publications where the person holds the primary authorship role.",
            "Indicates the number of books or specialized texts a person has released.",
            "Indicates the number of patents, useful solutions, or intellectual property rights a person has obtained.",
            "Denotes the number of national or international accolades or prizes received for artistic or athletic achievements.",
            "Indicates commendations, certificates of merit, or official recognition received."
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

    # entity_df.to_csv("./entities.csv", index=False, encoding="utf-8")
    relation_df.to_csv("relationships_test.csv", index=False, encoding="utf-8")
    


if __name__ == "__main__":
    default_schema()