import csv
with open('normDCIconvshift.csv', 'r') as f:
    reader = csv.reader(f)
    your_list = list(reader)[0]

print(your_list)