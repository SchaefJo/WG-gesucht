import requests
import pickle
import random
import re
import smtplib
import time
from bs4 import BeautifulSoup

def request(url, proxy_list, ua=[]):  #request.get but with proxy and user agent
    #for first scrape until time file is developed
    ua.append("Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0")
    while True:  #until one proxy worked
        proxy = proxy_list[random.randint(0, len(proxy_list)-1)]
        try:
            if len(ua) == 0:
                page = requests.get(url, proxies={"http":proxy, "https":proxy}, timeout = 5)
            else:
                headers = {"User-Agent":ua[random.randint(0,len(ua)-1)]}
                page = requests.get(url, proxies={"http":proxy, "https":proxy}, timeout = 5, headers = headers)
            break
        except OSError:
            pass
    return page

def email_config():
    print_mail_details()
    while True: #until true input
        change = input("Do you want to change your mail details? 0 for no, 1 for yes. Password will be visible!: ")
        if change == "0":
            break
        elif change == "1":
            your_mail = input("Your gmail: ") #save mails and password in files for future crawls
            send_to = input("Send mail to: ")
            pwd = input("Password: ")
            with open("your_mail", "wb") as f:
                pickle.dump(your_mail, f)
            with open("send_to", "wb") as f:
                pickle.dump(send_to, f)
            with open("pwd", "wb") as f:
                pickle.dump(pwd, f)
            break
        elif change == "break": #to get out of infinity loop
            break
        else:
            print("Wrong input")
            
def print_mail_details():
    #try to open file, if error it doesnt exist
    try:
        with open("your_mail", "rb") as f:
            print(pickle.load(f))
    except:
        print("you haven't added your mail yet")
    try:
        with open("send_to", "rb") as f:
            print(pickle.load(f))
    except:
        print("you haven't added the mail adress you want to get the emails with yet")
    try:
        with open("pwd", "rb") as f:
            print(pickle.load(f))
    except:
        print("you haven't added a password yet")  

def read_proxy_file():  #either updates proxies or just loads proxies
    while True:
        renew = int(input("Want to renew your proxies? 1 yes, 0 no: "))
        if renew == 1:  #updates
            proxy_list = get_proxies()
            with open("proxy_list","wb") as f: #save
                    pickle.dump(proxy_list, f)
            break
        elif renew == 0: 
            try:  #try to load proxy file
                with open("proxy_list","rb") as f:
                    proxy_list = pickle.load(f)
                print("open proxy file")
                break
            except:  #if no proxy file exists get proxies from website
                proxy_list = get_proxies()
                with open("proxy_list","wb") as f:
                    pickle.dump(proxy_list, f)
                break
        else:
            print("Wrong input")
    return proxy_list

def get_proxies():  #scrapes proxy list from a website
    page = requests.get("https://free-proxy-list.net/")
    page.raise_for_status()
    soup = BeautifulSoup(page.content,"html.parser")
    proxy_list = []
    all_proxies = soup.find_all("td")[:2400]
    for i in range(int(len(all_proxies)/8)):
        if all_proxies[i*8+4].get_text() == "elite proxy":
            proxy_list.append(all_proxies[i*8].get_text()+':'+all_proxies[i*8+1].get_text())   
    return proxy_list

def read_agent_file():  #either updates proxies or just loads proxies
    while True:
        renew = int(input("Want to renew your user agents? Takes 10-20 minutes 1 yes, 0 no: "))
        if renew == 1:  #update
            agent_list = reload_user_agents()
            with open("useragent_list","wb") as f: #save
                    pickle.dump(agent_list, f)
            break
        elif renew == 0:
            try:  #try to open useragent file
                with open("useragent_list","rb") as f:
                    agent_list = pickle.load(f)
                print("open user agent file")
                break
            except:  #if no useragent file exists get useragents from website
                agent_list = reload_user_agents()
                with open("useragent_list","wb") as f:
                    pickle.dump(agent_list, f)
                break
        else:
            print("Wrong input")
    return agent_list

def reload_user_agents():  #get useragents from different sources
    agent_list = []
    [agent_list.append(i) for i in get_agents("https://developers.whatismybrowser.com/useragents/explore/hardware_type_specific/computer/", proxy_list)]
    print("successfull computer user_agent")
    [agent_list.append(i) for i in get_agents("https://developers.whatismybrowser.com/useragents/explore/hardware_type_specific/mobile/", proxy_list)]
    print("successfull mobile user_agent")
    [agent_list.append(i) for i in get_agents("https://developers.whatismybrowser.com/useragents/explore/hardware_type_specific/phone/", proxy_list)]
    print("successfull phone user_agent")
    [agent_list.append(i) for i in get_agents("https://developers.whatismybrowser.com/useragents/explore/hardware_type_specific/tablet/", proxy_list)]
    print("successfull with all user_agents")
    return agent_list

def get_agents(url, proxy_list):  #scrapes user agents from website
    agent_list = []
    while True: 
        print("new page scraped")
        breaker = 0
        if len(agent_list) == 0:  #request without user agents (first time)
            page = request(url, proxy_list)
        else:
            page = request(url, proxy_list, ua = agent_list)
        try:  #try whether website has detetcted the scraper 
            page.raise_for_status()
        except:  #when detected return agent_list
            print("detected")
            return agent_list
        soup = BeautifulSoup(page.content, "html.parser")
        for i in soup.find_all("tr")[1:]:
            table_fields = i.find_all("td")
            if (table_fields[4].get_text() == "Very common") or (table_fields[4].get_text() == "Common"):
                agent_list.append(table_fields[0].get_text())
            else:
                breaker = 1
                break
        if breaker == 1:
            break  
        #next page
        url = "https://developers.whatismybrowser.com"+soup.find_all("div", id="pagination")[0].find_all("a", href=True)[-2]['href']   
    return agent_list

def get_ids(url, proxy_list, agent_list): #returns wg-gesucht apartment ids
    page = request(url, proxy_list, agent_list)
    try:
        page.raise_for_status()
    except:
        print("Error loading page")
    soup = BeautifulSoup(page.content,'html.parser')
    html = list(soup.children)[2]
    body = list(html.children)[3]
    listingRegex = re.compile(r'liste-details-ad-hidden-(\d+)')
    aptID = listingRegex.findall(str(body))
    return aptID

def check_ids(new_ids):
    try:  #check whether id file exists
        with open("ids","rb") as f:
            ids = pickle.load(f)
    except:
        ids = {}
    email = "\n"
    for i in new_ids:
        try: #if dictionary of id doesnt give an error its in the dict and therefore not new
            ids[i]
        except KeyError:
            email += "http://www.wg-gesucht.de/"+str(i)+".html\n"
            ids[i] = 1
    with open("ids","wb") as f: #save ids
        pickle.dump(ids, f)
    send_mail(email)
    
def send_mail(msg):
    #try opening your mail details
    try:
        with open("your_mail", "rb") as f:
            your_mail = pickle.load(f)
    except:
        your_mail = input("Something wrong with your gmail adress, type gmail again: ")
        with open("your_mail", "wb") as f:
            pickle.dump(your_mail, f)
    try:
        with open("send_to", "rb") as f:
            send_to = pickle.load(f)
    except:
        send_to = input("Something wrong with your send to adress, type mail adress again: ")
        with open("send_to", "wb") as f:
            pickle.dump(send_to, f)
    try: 
        with open("pwd", "rb") as f:
            pwd = pickle.load(f)
    except:
        pwd = input("Something went wrong with your password, type again: ")
        with open("pwd", "wb") as f:
            pickle.dump(pwd, f)
    
    #mail sever that sends "msg" from "your_mail" to "send_to"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(your_mail, pwd)
    server.sendmail(your_mail, send_to, msg)
    server.close()     

email_config()    
proxy_list = read_proxy_file()
agent_list = read_agent_file()
url = input("wg-gesucht url, default search if empty: ").strip()
if len(url) == 0:
    url = "https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.1.0.html?offer_filter=1&noDeact=1&city_id=90&category=0&rent_type=2&rMax=700&wgSea=2&wgAge=20&wgArt%5B1%5D=1&wgArt%5B11%5D=1&wgArt%5B0%5D=1&exc=2"
while True:
    ids = get_ids(url, proxy_list, agent_list)
    print(ids)
    check_ids(ids)
    sleep_time = 2400+random.randint(-600,600)
    print(sleep_time)
    time.sleep(sleep_time)