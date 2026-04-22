
import requests

WHATSAPP_TOKEN = "EAA4RhOEd6pEBRF9BZAJaTrvO6ZBmFb0VPtSAzHSJP1LuNuhlohvRwxFDCZBSiCiZAlVcHCZAZAU5tx7Ob3QkCob5hffk2oCvk5d7ZBp5t1UePscGWzHAqny4l8N3J727vZCUihu65t519dz8AwZB2ob3yc0Gjt3k7b5NoErLtbvDIZB9IJZBFnSw8WEUrCMeNDEzoZARtyEqEezhlGK0vJOxVe7NFXaU1XmCUhX2VRBlBac0"
PHONE_NUMBER_ID = "1025236267348548"
whatsapp_user = "6287798705864"

url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
headers = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}
data = {
    "messaging_product": "whatsapp",
    "to": whatsapp_user,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {"code": "en_US"},
    }
}
                  
response = requests.post(url, headers=headers, json=data, timeout=30)
print(response.json())
  