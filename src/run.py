from KG_builder.builder import KG_builder


if __name__ == "__main__":

    PATH = "/Users/huynhnguyen/WorkDir/bachoc_1/data/(16879491024946_28_06_2024_11_07)nguyen-thuong-nghia-1964-01-01-1719547648.txt"
    
    args = {
        "enities_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/entities.csv",
        "relation_schema" : "/Users/huynhnguyen/WorkDir/bachoc_1/relationships.csv",
        "threshold" : 0.6
    }
    
    corpus =  open(PATH, "r").read()
    
    from KG_builder.utils.clean_data import clean_vn_text
    
    corpus = clean_vn_text(corpus)
    
    # print(corpus)
    
    builder = KG_builder(**args)
    
    # print(
    new_triples = builder.run(corpus)
    builder.write_schema("new_relationship.csv")
    import json
    
    with open("new_triples.json", "w", encoding="utf-8") as f:
        json.dump(new_triples, f, ensure_ascii=False, indent=2)

