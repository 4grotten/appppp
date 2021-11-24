import re


class IndexServices:

    @staticmethod
    def remove_bad_char(symbols: str):
        symbols = symbols.replace('ё', 'е')
        symbols = symbols.replace('Ё', 'Е')
        return symbols

    @staticmethod
    def change_layout(string: str):
        char_map = (
            ("a", "ф"), ("c", "с"), ("d", "в"), ("e", "у"), ("b", "и"), ("f", "а"), ("g", "п"), ("h", "р"), ("i", "ш"),
            ("j", "о"), ("k", "л"), ("l", "д"),
            ("m", "ь"), ("n", "т"), ("o", "щ"), ("p", "з"), ("r", "к"), ("s", "ы"), ("t", "е"), ("u", "г"), ("v", "м"),
            ("w", "ц"), ("x", "ч"), ("y", "н"),
            ("z", "я"), ("A", "Ф"), ("B", "И"), ("C", "С"), ("D", "В"), ("E", "У"), ("F", "А"), ("G", "П"), ("H", "Р"),
            ("I", "Ш"), ("J", "О"), ("K", "Л"),
            ("L", "Д"), ("M", "Ь"), ("N", "Т"), ("O", "Щ"), ("P", "З"), ("R", "К"), ("S", "Ы"), ("T", "Е"), ("U", "Г"),
            ("V", "М"), ("W", "Ц"), ("X", "Ч"),
            ("Y", "Н"), ("Z", "Я"), ("[", "х"), ("]", "ъ"), (";", "ж"), ("<", "б"), (">", "ю"), ("й", "q"), ("Й", "Q")
        )
        re_forbidden_chars = re.compile(r"[\]\[<>]")
        invert_str, invert_str_list = '', []
        for char in string:
            char_ready = False
            for match in char_map:
                if char == match[0]:
                    invert_str_list.append(match[1])
                    char_ready = True
                elif char == match[1]:
                    if re_forbidden_chars.match(match[0]):
                        # ignore some chars
                        invert_str_list.append(char)
                    else:
                        invert_str_list.append(match[0])
                        char_ready = True
            if not char_ready:
                invert_str_list.append(char)
        return "".join(invert_str_list)