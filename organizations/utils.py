class JSONQuerySet(list):

    def filter(self, **kwargs):
        result = self
        for key, value in kwargs.items():
            result = [obj for obj in result if obj.get(key) == value]

        return JSONQuerySet(result)
