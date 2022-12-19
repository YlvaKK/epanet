class CSVWriter:

    def __init__(self, filename):
        self.filename = filename

    def writeLines(self, lines):
        self.f = open(self.filename, "w")

        for line in lines:
            self.f.write("{}\n".format(line))

    def close(self):
        self.f.close()