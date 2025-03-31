import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8'))
'''
5Pwk1wsodNGz6-HYfzcCf9voH6ZaSkeFffVooL_vVHs=
'''