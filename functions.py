import requests, netifaces
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup


def check(req):
    print("Request:", req.request)
    print("Status:", req.status_code)
    print("URL:", req.url)
    print("Headers:", req.headers)
    print("Content:", req.content)
    print("Cookies:", req.cookies)
    print("Reason:", req.reason)


def get_dhcp_data(user, password, cookies, dhcp_table_url, ip_info_cgi):
    print("Obtaining DHCP data...")
    requests.get(dhcp_table_url, cookies=cookies, auth=HTTPBasicAuth(user, password))
    ip_info = requests.get(ip_info_cgi, cookies=cookies, auth=HTTPBasicAuth(user, password))

    print("DHCP data obtained. Cleaning up data...")
    # Convert text from router cgi request response to list of lists
    ips = []

    ip_info_split = ip_info.text.split(";\n")
    for i in ip_info_split:
        i = i.replace("\n", "")
        i = i.replace("'", "")
        i = i.replace("var ", "")
        i = i.split(" = ")
        ips.append(i)

    # Strip out the un-needed data which doesn't relate to DHCP-assigned IP addresses
    x = 0
    while x <= 105:
        del ips[0]
        x += 1

    del ips[-1]

    # Clean up the DHCP data and make a dictionary of dictionaries
    num_devices = int(len(ips) / 7)
    dev_info = []

    ip_dict = {}
    for key, value in ips:
        ip_dict[key] = value

    count = 0
    while count < num_devices:
        device = {"ClientID": count, "ip": ip_dict.get("allClient" + str(count) + "_ip"),
                  "mac": ip_dict.get("allClient" + str(count) + "_mac"),
                  "hostname": ip_dict.get("allClient" + str(count) + "_hostname"),
                  "type": ip_dict.get("allClient" + str(count) + "_type"),
                  "types": ip_dict.get("allClient" + str(count) + "_types"),
                  "add": ip_dict.get("allClient" + str(count) + "_add"),
                  "active": bool(int(ip_dict.get("allClient" + str(count) + "_active")))}
        dev_info.append(device)
        count += 1

    return dev_info


def get_homeplug_ip(dev_info):
    for dev in dev_info:
        if dev["hostname"] == "XWN5001":
            print("HomePlug's IP is:", dev["ip"])
            return dev["ip"]


def get_my_ip(dev_info):
    print("Getting your IP...")
    local_ifs = netifaces.interfaces()
    for dev in dev_info:
        for interface in local_ifs:
            info = netifaces.ifaddresses(interface)
            try:
                mac = info[netifaces.AF_LINK][0]['addr'].upper()

                if dev["mac"] == mac:
                    print("Your IP is:", dev["ip"])
                    return {"ip": dev["ip"], "connection": dev["type"]}
            except:
                pass


def homeplug_reboot(homeplug_ip, user, password):
    url = "http://" + homeplug_ip + "/reboot.htm"

    connect = requests.get(url, auth=HTTPBasicAuth(user, password))

    soup = BeautifulSoup(connect.text, "html.parser")
    reboot_url = soup.form['action']

    reboot = requests.post("http://" + homeplug_ip + reboot_url, data={"submit_flag": "reboot", "yes": "Yes"},
                           auth=HTTPBasicAuth(user, password))
    if reboot.status_code == "200":
        print("XWN5001 rebooting...")
    else:
        print("Error rebooting XWN5001.")


def router_reboot(reboot_url, cookies, user, password):
    reboot = requests.get(reboot_url, cookies=cookies, auth=HTTPBasicAuth(user, password))

    if reboot.status_code == "200":
        print("Router rebooting...")
    else:
        print("Error rebooting router.")

    return reboot