project = "Vehicle (sysml2-kit example)"
extensions = ["sphinx_needs"]
exclude_patterns = ["_build"]
# types, links, fields and the RFLP rules live in ubproject.toml / schemas.json, shared with ubCode
needs_from_toml = "ubproject.toml"
