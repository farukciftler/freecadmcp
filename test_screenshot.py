import xmlrpc.client
import json

proxy = xmlrpc.client.ServerProxy("http://127.0.0.1:36875")
try:
    info = json.loads(proxy.get_system_info())
    print("System Info:", info)
    res = json.loads(proxy.get_view_screenshot("EvPlani"))
    print("Screenshot Result:", str(res)[:100])
except Exception as e:
    print("Error:", e)
