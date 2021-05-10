
class ParseString:

    def __init__(self, string):
        self.string_split = string.replace('\n', ';').split(';')

    @classmethod
    def host(self):
        return 'string_parser'

    def ingredients(self):

        ingredients = []
        for i in self.string_split:

            if len(i) > 1:
                ingredients.append(i)

        return ingredients

    @staticmethod
    def title():
        return 'not specified'

    @staticmethod
    def total_time():
        return 'not specified'

    @staticmethod
    def instructions():
        return 'no instructions'

    @staticmethod
    def image():
        return 'not specified'

    @staticmethod
    def nutrients():
        return {}

    @staticmethod
    def language():
        return 'not specified'

    @staticmethod
    def yields():
        return 'not specified'
