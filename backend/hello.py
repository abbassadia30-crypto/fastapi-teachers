from analysis import numeric_converter

data = [
    {"name": "Ali", "phone": "923401234567", "marks": "88"},
    {"name": "Usman", "phone": "03001112223", "marks": "75"}
]

final_data = numeric_converter(data)
print(final_data)