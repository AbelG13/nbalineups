import pandas as pd

additional_data = pd.read_csv('playersBDL25.csv')
first_name = "Yanic Konan"
last_name = "Niederhäuser"
height = additional_data[(additional_data['first_name'] == first_name) & (additional_data['last_name'] == last_name)]['height']
print(height)
