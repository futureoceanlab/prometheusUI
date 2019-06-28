import csv
with open('normDCIconvshift.csv', 'r') as f:
    reader = csv.reader(f)
    your_list = list(reader)[0]
    newList = []
    for i in your_list:
    	newList.append(float(i))

print(newList)