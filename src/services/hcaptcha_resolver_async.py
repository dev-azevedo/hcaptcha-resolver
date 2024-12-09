import google.generativeai as genai
import time
import PIL
import json
import os
import re
import asyncio

def filter_by_list(text: str) -> list[int]:
    numeros = re.findall(r'\d+', text)
    return [int(num) for num in numeros if 1 <= int(num) <= 9]

class HCaptchaResolver:
    def __init__(self, page):
        self.dir = os.path.dirname(__file__)
        self.position_images = {
            1: {"x": 830, "y": 390},
            2: {"x": 950, "y": 390},
            3: {"x": 1090, "y": 390},
            4: {"x": 830, "y": 530},
            5: {"x": 950, "y": 530},
            6: {"x": 1090, "y": 530},
            7: {"x": 830, "y": 660},
            8: {"x": 950, "y": 660},
            9: {"x": 1090, "y": 660}
        }

        self.page = page
        genai.configure(api_key='AIzaSyC1D37Jj3OdwqnKaGiyDx24GO5_8Kwjk40')
      
    async def consultar_grid_gemini(self): 
        recort_hcaptcha = os.path.join(self.dir, '..', 'images', 'grid_hcaptcha.png')
        img = PIL.Image.open(recort_hcaptcha)

        model = genai.GenerativeModel("models/gemini-1.5-flash")

        response = model.generate_content(
        [
        '''
            Analise a seguinte imagem que contém:
            1. Uma modal central com uma grade 3x3 (9 quadros)
            2. Possivelmente uma imagem de referência (top) localizada:
            - À direita do texto
            - Acima da grade 3x3

            Retorne um JSON estruturado da seguinte forma:
            {
                "top": "descrição da imagem de referência" (se existir),
                "grid": {
                    "1": "descrição do quadro 1",
                    "2": "descrição do quadro 2",
                    ...
                    "9": "descrição do quadro 9"
                }
            }

            Observações:
            - Numere os quadros da esquerda para direita, de cima para baixo (1-9)
            - Forneça descrições com detalhes voltados apenas para o objeto prinicipal
            - Omita o campo "top" se não houver imagem de referência
        ''', 
        img
        ])

        response.resolve()
        json_convert = response.text.strip("(```)")
        json_convert = json_convert.replace('json\n', '', 1).replace('```','')
        print(json_convert)
        json_convert = json.loads(json_convert)
        
        return json_convert

    async def consultar_gemini(self):
        answer_grid = await self.consultar_grid_gemini()
        
        recort_title_hcaptcha = os.path.join(self.dir, '..', 'images', 'title_hcaptcha.png')
        img = PIL.Image.open(recort_title_hcaptcha)

        model = genai.GenerativeModel("models/gemini-1.5-flash")

        response = model.generate_content(
        [
        f'''
            Nessa imagem que estou te enviando, possui um título em cima de um Grid 3x3 de quadros com imagens.
            Se houver uma imagem ao lado do título, desconsidere.
            Com esse título e o Objeto que estou enviando, me retorne, APENAS UMA LISTA, contendo os números dos quadros corretos, 
            com as opções disponíveis, de 1 a 9, as quais estão corretas.
            Se possuir no Objeto abaixo um campo top diferente de None, leve ele em consideração para responder a pergunta do titulo.
            {answer_grid}
        
            DESEJO A RESPOSTA DA IMAGEM ANALISADA, E NÃO UMA FUNÇÃO.
            
            O retorno esperado é uma lista com seus valores [n1, n2, ...], não tendo nenhuma outra mensagem ou palavra junto da lista.
        ''', 
        img
        ])

        response.resolve()
        
        return filter_by_list(response.text.strip("(```)"))
         
        pyautogui.click(x=1110, y=940, duration=0.5)
        await asyncio.sleep(2)
    
    async def select_images_hcaptcha(self, list_positions_frames):
        for index in list_positions_frames:
            position = self.position_images.get(index)
            if position:
                await self.page.mouse.click(position['x'], position['y'], button='left')
                print(f"Clicando no item '{index}' na posição x: {position['x']}, y: {position['y']}")
                await asyncio.sleep(1)
            else:
                print(f"Coordenadas não encontradas para a chave {index}")
    
    async def next_hcaptcha(self):
        print("Clicando no botão Avançar")
        await self.page.mouse.click(1100, 800, button='left')
        await asyncio.sleep(1)
    
    async def run(self):
        print("🫡 Resolvendo o hcaptcha")
        list_positions_frames = await self.consultar_gemini()
        if list_positions_frames:
            await self.select_images_hcaptcha(list_positions_frames)
            await asyncio.sleep(1)
            await self.next_hcaptcha()
            
        await asyncio.sleep(3)