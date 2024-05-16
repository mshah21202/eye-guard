def format_number_plate(plate_numbers: list[str]):
    '''
    Returns a formatted plate number

    Args:
        plate_number: List of strings containing a potential number plate

    Returns:
        plate_numbers: List of potential number plates
    '''
    # remove first element
    if len(plate_numbers) > 0:
        plate_numbers.pop(0)

    # supported countries
    supported_countries = {
        "JO": {
            "identifiers": ["JORDAN", "jordan", "الأردن", "الاردن"]
        },
        "SA": {
            "identifiers": ["KSA", "ksa", "السعودية"]
        },
        "KW": {
            "identifiers": ["KUWAIT", "Kuwait", "الكويت"]
        },
    }

    country_code = ""

    # Try to determine car nationality (Supports: Jordan, KSA, Kuwait)
    for text in plate_numbers:
        temp = text.lower()
        if temp in supported_countries["JO"]["identifiers"]:
            country_code = "JO"
        elif temp in supported_countries["SA"]["identifiers"]:
            country_code = "SA"
        elif temp in supported_countries["KW"]["identifiers"]:
            country_code = "KW"

    potential_plates = []
    # If determined car nationality then format
    if country_code == "JO":
        potential_plates = jordan_format(plate_numbers)
    elif country_code == "SA":
        potential_plates = sa_format(plate_numbers)
    elif country_code == "KW":
        potential_plates = jordan_format(plate_numbers)
    else:
        potential_plates = unknown_format(plate_numbers)
    
    return potential_plates


def jordan_format(strings: list[str]):
    '''
    Returns a list of potential jordan formatted plate numbers
    '''
    result = []

    strings = list(filter(lambda string: any(char.isdigit() for char in string) or '-' in string, strings))

    # if one string
    if len(strings) == 1:
        if ('-' in strings[0]):
            result.append(strings[0])
            return result
        
        if len(strings[0]) == 7:
            result.append(strings[0][:2] + '-' + strings[0][2:])
        else:
            result.append(strings[0][:2] + '-' + strings[0][2:])
            result.append(strings[0][:1] + '-' + strings[0][1:])
        
        return result
    
    
    # if two strings
    if len(strings[0] < strings[0]):
        result.append(strings[0] + '-' + strings[1])
        return result
    
    result.append(strings[1] + '-' + strings[0])
    return result

def sa_format(strings: list[str]):
    '''
    Returns a list of potential KSA formatted plate numbers
    '''
    identifiers = ["KSA", "ksa", "السعودية"]

    number_strings = list(filter(lambda string: any(char.isdigit() for char in string) and string.isascii(), strings))
    char_strings = list(filter(lambda string: any(not char.isdigit() and char != '+' for char in string) and string.isascii(), strings))

    numbers = ""
    chars = ""

    if len(number_strings) > 1:
        numbers = "".join(number_strings)
    else:
        numbers = number_strings[0]

    new_char_strings = []
    # Remove Identifiers
    for string in char_strings:
        if string in identifiers:
            continue
        
        new_char_strings.append(string)
    
    if len(new_char_strings) > 1:
        chars = "".join(new_char_strings)
    else:
        chars = new_char_strings[0]
    
    result_temp = chars + numbers

    return [result_temp]

    

def unknown_format(strings: list[str]):
    '''
    '''
    result = []

    strings = list(filter(lambda string: len(string) <= 5 and string.isascii(), strings))
    
    result.append("".join(strings))

    return result