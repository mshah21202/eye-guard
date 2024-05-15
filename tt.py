import re

def format_ocr_results(ocr_results):
    # Initialize an empty set to store seen IDs (avoid duplicates)
    seen_ids = set()
    formatted_results = []

    for string in ocr_results:
        # Remove non-ASCII characters
        string = re.sub(r'[^\x00-\x7F]+', '', string)

        # Split the string into lines (ensure empty lines are included)
        lines = string.splitlines()  # This handles empty lines within the string

        # Initialize variables
        formatted_line = ''
        potential_id = ''
        in_potential_id = False

        # Iterate through each line in the split string
        for line in lines:
            # Check if the line contains only digits and hyphens
            if re.match(r'\d+-?\d+', line):
                # If so, mark as potential ID and store
                potential_id = line
                in_potential_id = True
            elif in_potential_id:  # Check if currently processing a potential ID
                # If there's a potential ID and current line has content, combine them
                formatted_line = potential_id + ' ' + line.strip()
                potential_id = ''  # Reset potential ID and processing flag
                in_potential_id = False
            else:
                # If not part of potential ID, reset everything
                formatted_line = ''
                potential_id = ''
                in_potential_id = False

        # Handle cases where the ID is at the end without following text
        if potential_id:
            formatted_line = potential_id

        # Remove trailing spaces
        formatted_line = formatted_line.rstrip()

        # Check for duplicates before appending (using set)
        if formatted_line and formatted_line not in seen_ids:
            formatted_results.append(formatted_line)
            seen_ids.add(formatted_line)

    # Return the formatted results as a single string with spaces
    return ' '.join(formatted_results)


# Example usage
ocr_results_jordan = ["JORDAN\n45-78856\nالاردن", "JORDAN", "45-78856", "الاردن"]
ocr_results_jordan_2 = ['الاردن\n5\nJORDAN 12345', 'الاردن', '5', 'JORDAN', '12345']
ocr_results_ksa = ['ح نط ٧٦٥٣\n7653 TNJ\n*\nالسعودية\nKSA', 'ح', 'نط', '٧٦٥٣', '7653', 'TNJ', '*', 'السعودية', 'KSA']
ocr_results_kuwait = ['دولة الكويت\nKUWAIT\n14-40937', 'دولة', 'الكويت', 'KUWAIT', '14-40937']
ocr_results_kuwait_2 = ['دولة الكويت 10\nKUWAIT\n23456', 'دولة', 'الكويت', '10', 'KUWAIT', '23456']

formatted_results_jordan = format_ocr_results(ocr_results_jordan)
formatted_results_jordan_2 = format_ocr_results(ocr_results_jordan_2)
formatted_results_ksa = format_ocr_results(ocr_results_ksa)
formatted_results_kuwait = format_ocr_results(ocr_results_kuwait)
formatted_results_kuwait_2 = format_ocr_results(ocr_results_kuwait_2)

print(formatted_results_jordan)
print(formatted_results_jordan_2)
print(formatted_results_ksa)
print(formatted_results_kuwait)
print(formatted_results_kuwait_2)
