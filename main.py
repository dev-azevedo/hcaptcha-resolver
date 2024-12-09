import cv2
from rebrowser_playwright.async_api import async_playwright, Response, Geolocation
from PIL import Image
import pyautogui
import asyncio
import os

from src.services.hcaptcha_resolver_async import HCaptchaResolver

CHROME_ARGS = [    
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--window-size=1920,1080',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--disable-gpu',
    '--hide-scrollbars',
    '--suppress-message-center-popups'
]

async def create_undetected_browser():
    playwright = await async_playwright().start()
    
    # Use specific browser options to reduce detection
    browser = await playwright.chromium.launch(
        headless=False,
        channel='chrome',
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--hide-scrollbars',
            '--suppress-message-center-popups'
        ]
    )
    
    # Create a new context with additional stealth measures
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        geolocation=Geolocation(latitude=-25.4294, longitude=-49.2713 , accuracy=50),
        locale='pt-BR',
        permissions=['geolocation']
        # user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        # extra_http_headers={
        #     'Accept-Language': 'en-US,en;q=0.9',
        #     'Sec-Ch-Ua': '"Google Chrome";v="91", "Not A Brand";v="99"',
        #     'Sec-Ch-Ua-Mobile': '?0',
        # }
    )
    
    # Implement additional anti-detection techniques
    # await context.add_init_script("""
    #     Object.defineProperty(navigator, 'webdriver', {
    #         get: () => undefined
    #     });
        
    #     window.navigator.chrome = {
    #         runtime: {},
    #         loadTimes: function() {},
    #         csi: function() {},
    #         app: {}
    #     };
        
    #     delete Object.getPrototypeOf(navigator).webdriver;
    # """)
    
    page = await context.new_page()
    
    return playwright, browser, context, page
   
async def recort_image(page):
    await page.screenshot(path='./src/images/screenshot_resolve_hcaptcha.png')
    loop = asyncio.get_running_loop()
    image = await loop.run_in_executor(None, Image.open, './src/images/screenshot_resolve_hcaptcha.png')
    recort_image = await loop.run_in_executor(None, image.crop, (760, 250, 1160, 850))

    await loop.run_in_executor(None, recort_image.save, './src/images/grid_hcaptcha.png')
    
    recort_image_title = await loop.run_in_executor(None, image.crop, (760, 250, 1160, 360))
    await loop.run_in_executor(None, recort_image_title.save, './src/images/title_hcaptcha.png')
    print(f"Imagem recortada salva em: recort_screenshot.png")

def find_image_hcaptcha_on_screen():
    try:
        pyautogui.screenshot('./src/images/screenshot_hcaptcha.png')
    
        screenshowPgn = os.path.join(os.path.dirname(__file__), 'src', 'images', 'screenshot_hcaptcha.png')
        templatePng = os.path.join(os.path.dirname(__file__), 'src', 'images', 'hcaptcha_example.png')
        
        screenshot = cv2.imread(screenshowPgn, cv2.IMREAD_UNCHANGED)
        template = cv2.imread(templatePng, cv2.IMREAD_UNCHANGED)
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= 0.8:
            return True
        else:
            return False
    except:
        return False
    
async def main(certificado):
    playwright, browser, context, page = await create_undetected_browser()
    
    hcaptcha_rosolver = HCaptchaResolver(page=page)
    login_response: Response = None
    counter: int = 0
    
    try:
        # Navigate to a website
        await page.goto('https://login.esocial.gov.br/login.aspx')

        await page.locator('css=#login-acoes > div.d-block.mt-3.d-sm-inline.mt-sm-0.ml-sm-3 > p > button').click()
        
        await page.wait_for_timeout(5000)
        
        # async def on_res(res: Response):
        #     nonlocal login_response, counter
        #     if res.status and res.url.startswith("https://certificado.sso.acesso.gov.br/login"):
        #         login_response = res
                
        #     if res.status == 200 and res.url.startswith("https://imgs.hcaptcha.com/"):
        #         counter += 1
                
        
        # page.on("response", on_res)
        
        await page.locator('css=#login-certificate').click()
        
        await page.wait_for_timeout(1000)
        
        while True:
            print("Aguardando hCaptcha")
            has_hcaptcha = find_image_hcaptcha_on_screen()
            await asyncio.sleep(1)
            
            if has_hcaptcha:
                await recort_image(page=page)
                await hcaptcha_rosolver.run()
            else:
                print('Hcaptcha não encontrado.')
                break
        
        print("Selecionando certificado")
        await asyncio.sleep(3)
        # Precionar a tecla up
        pyautogui.press('up')
        print("UP")
        
        await asyncio.sleep(.5)
        if certificado == 1:
            print("Selecionando certificado WHP")
            pyautogui.press('down')
        elif certificado == 2:
            print("Selecionando certificado TJT")
            pyautogui.press('down')
            pyautogui.press('down')
            
            
        pyautogui.press('enter')
        print("ENTER")
        
        await asyncio.sleep(5)
        print("Terminou")
        
        
    
    finally:
        await browser.close()
        await playwright.stop()
    
async def process_hcaptcha(page, hcaptcha_rosolver):
    try:
        await recort_image(page=page)
        await hcaptcha_rosolver.run()
        return True
    except Exception as e:
        print(f"Erro ao processar hCaptcha: {e}")
        return False

asyncio.run(main(1))
