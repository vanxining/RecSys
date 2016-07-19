
raw = open(__file__).read().strip()
raw = raw[raw.index("topn" + " "):]

# "topn" **MUST** be the first attribute

topn = 30
normalize_dataset = False
classifier = "LR"

if classifier == "MLP":
    normalize_dataset = True
