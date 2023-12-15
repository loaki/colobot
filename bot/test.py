from dateutil import relativedelta
from datetime import datetime

# d = datetime.now()
# wd = d.weekday()
# for i in range(0,500):
#     d += relativedelta.relativedelta(weeks=1)
#     if d.weekday() != wd:
#         print(d.strftime("%d %a %m"))
# print(datetime.weekday())
# now = datetime.now()
# offset = 
# startDate = now + relativedelta
hour = 12
d = 10
m = 12
weekday = 0
year = 2023

date = datetime.strptime(f"{hour}-{d}-{m}-{year}", "%H-%d-%m-%Y")
offset = 7 - date.weekday()
date += relativedelta.relativedelta(days=offset)
print(date)