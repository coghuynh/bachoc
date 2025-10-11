
from KG_builder.utils.clean_data import read_schema, read_json


if __name__ == "__main__":
    schema_str, schema = read_schema("/Users/huynhnguyen/WorkDir/bachoc_1/entities.csv")
    result = read_json("/Users/huynhnguyen/WorkDir/bachoc_1/new_sample_entities.json")
    
    for element in result:
        value = element[""]
