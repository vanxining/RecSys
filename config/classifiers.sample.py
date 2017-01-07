path = __file__
if path[-1] == 'c':
    path = path[:-1]

raw = open(path).read().strip()
raw = raw[raw.index("topn" + " "):]

# "topn" **MUST** be the first attribute

topn = 30
normalize_dataset = False

# NB, LR, MLP
classifier = "LR"

if classifier == "MLP":
    normalize_dataset = True
