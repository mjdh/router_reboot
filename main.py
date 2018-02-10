"""
====================
Router Reboot Script
====================

Author: Michael Henley (michael@henley.co)
Date: 10 February 2018

A script to programmatically reboot a DSL-3780 (TalkTalk) router and a Netgear XWN5001 Wifi HomePlug.

A separate file, secrets.py, should contain the IP address of your router as "router_ip", the router's
login credentials ("user", "password"), and the HomePlug's login credentials ("hp_user", "hp_password").

Non-standard dependencies: BeautifulSoup; netifaces.

"""

import requests
from requests.auth import HTTPBasicAuth
from functions import check, get_homeplug_ip, get_dhcp_data, get_my_ip, homeplug_reboot, router_reboot
from Secrets.secrets import *

base_url = "http://" + router_ip
reboot_url = base_url + "/cgi-bin/MAINTENANCE/reboot_wait.asp"
dhcp_table_url = base_url + "/cgi-bin/SETUP/sp_lan.asp"
ip_info_cgi = base_url + "/cgi-bin/get/SETUP/sp_lan.cgi"

running = True

while running:

    run1 = requests.get(base_url)

    # Check that this is the right network
    if run1.headers["WWW-Authenticate"] != 'Basic realm="DSL-3780"':
        print("Not on DSL-3780 network")
        running = False

    # If it's the right network, save the cookie and log in to the router
    else:
        cookies = run1.cookies

        router_req = requests.get(base_url, cookies=cookies, auth=HTTPBasicAuth(user, password))

        # Find the IP address for the HomePlug
        if router_req.reason == "OK":
            print("Logged into router.")

            dhcp_data = get_dhcp_data(user, password, cookies, dhcp_table_url, ip_info_cgi)
            homeplug_ip = get_homeplug_ip(dhcp_data)
            local_ip = get_my_ip(dhcp_data)

            confirm = input("Are you sure you want to reboot? Type 'Yes' or 'No'")

            if confirm.lower() == "yes":
                # If connecting via the HomePlug, reboot the router first and then the HomePlug
                if local_ip["connection"] == "Ethernet":
                    print("Ethernet connection")
                    router_reboot(reboot_url, cookies, user, password)
                    homeplug_reboot(homeplug_ip, hp_user, hp_password)

                # If connecting via the router, reboot the HomePlug first and then the router
                if local_ip["connection"] == "802.11":
                    print("Wifi connection")
                    homeplug_reboot(homeplug_ip, hp_user, hp_password)
                    router_reboot(reboot_url, cookies, user, password)

                running = False

            if confirm.lower() == "no":
                print("Cancelling without rebooting.")
                running = False

        else:
            print("Error authenticating with router. Stopping!")
            running = False
