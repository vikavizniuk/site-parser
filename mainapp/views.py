from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from collections import deque


def normalizedUrl(url):
    if not (url.endswith("/") or url.endswith(".pdf")):
        url += "/"
    return url

def mainapp(request):
    if request.method == "POST": 
        
        domen_url = request.POST.get("inputURL")
        parsed_domen_url = urlparse(domen_url)
        print(parsed_domen_url)
        if parsed_domen_url.scheme == '' or parsed_domen_url.netloc == '':
            return render(request, "mainapp/mainapp.html", {"error": "Enter correct domen URL (https://...)"})
        if parsed_domen_url.path not in ("", "/"):
            return render(request, "mainapp/mainapp.html", {"error": "Enter domen URL"})
        
        domen_url = normalizedUrl(domen_url)
        try:
            data = requests.get(domen_url, timeout=(5,10))
            data.raise_for_status()
        except requests.RequestException as e:
            return render(request, "mainapp/mainapp.html", {"error": str(e)})
        visited = set()   

        def deep_tree(current_url, parent_elem):
            if current_url not in visited:
                duplicates = set()
                visited.add(current_url)
                try:
                    data = requests.get(current_url, timeout=(5,10))
                    data.raise_for_status()
                except requests.RequestException as e:
                    print(e)
                    return 
                soup = BeautifulSoup(data.text, "lxml")
                chosen_links = soup.find_all("a") 
                for l in chosen_links:
                    if l.has_attr("href"):
                        link_href = str(l["href"])
                        link_href = link_href.split("#")[0].split("?")[0]
                        joined_link = urljoin(current_url, link_href)
                        joined_link = normalizedUrl(joined_link)
                        parsed_link = urlparse(joined_link)
                        
                        if "cdn-cgi" in parsed_link.path or "email-protection" in parsed_link.path or joined_link in duplicates:
                            continue

                        duplicates.add(joined_link)
                        if parsed_link.netloc == parsed_domen_url.netloc:
                            new_parent = ET.SubElement(parent_elem, "link", attrib={"url": parsed_link.geturl()})
                            if len(visited) < 5:
                                deep_tree(joined_link, new_parent)

        root = ET.Element("site", attrib={"url": domen_url})
        
        deep_tree(domen_url, root)
        
        
        response = ET.tostring(root)
        return HttpResponse(response, content_type="application/xml")
    return render(request, "mainapp/mainapp.html")