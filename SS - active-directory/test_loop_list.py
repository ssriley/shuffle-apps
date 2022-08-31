import re


matches = []
txt = ["SIP:corey.williams@safesystems.com","smtp:c.williams@safesystems.com","X500:/o=ExchangeLabs/ou=Exchange Administrative Group (FYDIBOHF23SPDLT)/cn=Recipients/cn=c463defe55a548f49494c043f19ca2bd-Corey Willi","smtp:corey@safesystems.com","SMTP:Corey.Williams@safesystems.com"]
for item in txt:
    x = re.search("(?i)smtp:([^,]*$)", item)
    if x:
        matches.append(x.string)
if x:
  print(str(matches))
else:
  print("No match")