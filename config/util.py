import re


kv_pattern = re.compile(r'(\w+)\s*=\s*(.+)')


def get_py_config_file_content(path):
    if path[-1] == 'c':
        path = path[:-1]

    raw = open(path).read().strip()
    return raw[raw.rindex("_config"):]


class AttribValue(object):
    def __init__(self, raw):
        self.wrap = ""
        if raw and (raw[0] == '"' or raw[0] == "'"):
            self.wrap = raw[0]
            raw = raw[1:-1]

        self.value = raw

    def __str__(self):
        return self.wrap + self.value + self.wrap

    def __repr__(self):
        return self.__str__()


class PyConfigFile(object):
    def __init__(self, fpath):
        self.fpath = fpath
        if fpath[-1] == 'c':
            self.fpath = fpath[:-1]

        self.lines = []
        self.attrib = []

        for line in open(fpath):
            line = line.rstrip()
            self.lines.append(line)

            if line:
                match = kv_pattern.match(line)
                if match and match.group(1) not in ("_config", "raw",):
                    self.attrib.append((match.group(1), AttribValue(match.group(2))))

    def sync(self, m):
        for key, val in self.attrib:
            val.value = str(getattr(m, key))

    def save(self):
        m = {key: val for key, val in self.attrib}

        with open(self.fpath, 'w') as outf:
            for index, line in enumerate(self.lines):
                if line:
                    match = kv_pattern.match(line)
                    if match:
                        key = match.group(1)
                        if key in m:
                            self.lines[index] = key + " = " + m[key]

                outf.write(line + '\n')
