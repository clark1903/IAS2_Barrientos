with open("reports/urls.py", "r") as f:
    content = f.read()

content = content.replace("add_intervention,", "add_intervention,\n    add_case_comment,")

with open("reports/urls.py", "w") as f:
    f.write(content)
