# very simple class to streamline output writing
class CSVWriter:
    f = None
    filename = None

    def __init__(self, filename):
        self.filename = filename

    def write_lines(self, lines):
        self.f = open(self.filename, "w")

        for line in lines:
            self.f.write("{}\n".format(line))

    def close(self):
        self.f.close()
