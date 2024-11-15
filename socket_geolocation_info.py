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
        # ipinfo.io API를 통해 IP 주소 정보 요청
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        
        # API 응답이 성공적인지 확인
        if response.status_code == 200:
            data = response.json()
            
            # 필요한 정보 추출
            return {
                "IP": data.get("ip"),
                "City": data.get("city"),
                "Region": data.get("region"),
                "Country": data.get("country"),
                "Location (Lat, Long)": data.get("loc"),  # 위도, 경도
                "ISP (Organization)": data.get("org"),
                "Timezone": data.get("timezone")
            }
        else:
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None
    

'''
geo_info = get_geolocation("127.0.0.1")
location = f"{geo_info['City']}, {geo_info['Region']}, {geo_info['Country']}" if geo_info else "Unknown"
print(location)
'''