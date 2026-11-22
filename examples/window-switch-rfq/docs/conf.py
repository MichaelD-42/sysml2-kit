project = "Seat switch RFQ (sysml2-kit example)"
extensions = ["myst_parser", "sphinx_needs"]
# _generated holds pages included into others (compliance.md), not documents of their own
exclude_patterns = ["_build", "_generated"]
# Markdown needs as ::: fences
myst_enable_extensions = ["colon_fence"]
# types, links, fields and the RFLP rules live in ubproject.toml / schemas.json, shared with ubCode
needs_from_toml = "ubproject.toml"
