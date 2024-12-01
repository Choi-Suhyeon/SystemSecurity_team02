import psutil
import time
import requests

def get_geolocation(ip_address):
    '''
    [explain]
        주어진 IP 주소에 대한 지리 정보를 반환하는 함수
    [param]
        ip_address : 지리 정보를 조회할 IP 주소
    [return]
        geolocation : 딕셔너리 (없는 경우 None)
    '''   
    
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")

        if response.status_code != 200:
            return None
        
        data = response.json()
        
        return {
            "ip": data.get("ip"),
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "location": data.get("loc"),
            "isp": data.get("org"),
            "timezone": data.get("timezone")
        }
    except Exception as e:
        return None
    

# geo_info = get_geolocation("223.130.192.247")
# location = f"{geo_info['City']}, {geo_info['Region']}, {geo_info['Country']}" if geo_info else "Unknown"
# print(location)
