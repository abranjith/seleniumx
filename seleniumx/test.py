import asyncio
import sys
sys.path.append("..\\seleniumx")
import httpx
from seleniumx.webdriver.chrome.webdriver import ChromeDriver
from seleniumx.webdriver.common.by import By

print(sys.modules['seleniumx'])

def for_else(n):
    print(__name__)
    for i in range(n):
        if i == 5:
            break
        print(i)
    else:
        print("no break")

async def post():
    j = {'capabilities': {'firstMatch': [{}], 'alwaysMatch': {'browserName': 'chrome', 'platformName': 'any', 'pageLoadStrategy': 'normal', 'goog:chromeOptions': {'extensions': [], 'args': []}}}, 
        'desiredCapabilities': {'browserName': 'chrome', 'version': '', 'platform': 'ANY', 'pageLoadStrategy': 'normal', 'goog:chromeOptions': {'extensions': [], 'args': []}}}
    h = {'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8', 'User-Agent': 'selenium/4.0.0a5 (python windows)', 'Connection': 'keep-alive'}
    u =  "http://localhost:54762"
    p = "/session"
    cl = httpx.AsyncClient(base_url=u)
    #async with cl as c:
    r = await cl.post(p, params=None, json=j, headers=h)
    await cl.aclose()
    print(r.text)

async def get():
    h = {'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8', 'User-Agent': 'selenium/4.0.0a5 (python windows)', 'Connection': 'keep-alive'}
    u =  "http://localhost:54762"
    p = "/status"
    cl = httpx.AsyncClient()
    cl.base_url = httpx.URL(u)
    #async with cl as c:
    r = await cl.get(p, params=None, headers=h)
    await cl.aclose()
    print(r.text)


async def selenium_test():
    p = r"C:\Users\Ranjith\pybrowser\browserdrivers\chromedriver.exe"
    d = await ChromeDriver.create(executable_path = p)
    await d.get("http://www.google.com")
    title = await d.title
    print(title)
    search_box = await d.find_element(by=By.NAME, value="q")
    await search_box.send_keys("seleniumx rocks")
    await asyncio.sleep(10)
    await d.close()
    await d.quit()

if __name__ == "__main__":
    #for_else(5)
    #asyncio.run(selenium_test())
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    #loop.run_until_complete(selenium_test())
    loop.run_until_complete(get())