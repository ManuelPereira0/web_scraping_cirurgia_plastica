import re
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import pymysql.cursors

def iniciar_driver():
    driver = webdriver.Firefox()
    driver.get("https://www.cirurgiaplastica.org.br/encontre-um-cirurgiao/")
    return driver

# Função para criar uma conexão com o banco de dados
def criar_conexao():
    return pymysql.connect(
        host='seu host',
        user='seu user',
        database='seu database',
        password='sua password',
        cursorclass=pymysql.cursors.DictCursor
    )

contador_registro = 1

conexao = criar_conexao()
cursor = conexao.cursor()

ufs = ["SP", "TO"]

driver = iniciar_driver()

for uf in ufs:
    sleep(1)
    botao_buscar = driver.find_element(By.XPATH, "/html/body/div[4]/div[1]/div/div/div[1]/div[2]/div/div/div/a")
    botao_buscar.click()
    sleep(1)
    pesquisa = driver.find_element(By.XPATH, '//*[@id="cirurgiao_uf"]')
    sleep(0.5)
    pesquisa.send_keys(uf)
    sleep(0.5)
    botao_pesquisa = driver.find_element(By.XPATH, '//*[@id="cirurgiao_submit"]')
    botao_pesquisa.click()
    sleep(2)
    
    while True: 
        divs = driver.find_elements(By.CLASS_NAME, "cirurgiao-results-item")

        if not divs:
            print("Divs não encontradas")
        else:
            print("........................................")
            for div in divs:
                try:
                    sleep(1)   
                    link = div.find_element(By.TAG_NAME, "a")
                    try:
                        link.click()
                        sleep(1)
                    except:
                        sleep(2)
                        link.click()
                        sleep(1)
                
                    pagina_html = driver.page_source

                    soup = BeautifulSoup(pagina_html, 'html.parser')
                    
                    texto_div = ''
                    
                    div_cirurgiao_details = soup.find('div', class_='cirurgiao-details')
                    if div_cirurgiao_details:
                        texto_div = div_cirurgiao_details.get_text(separator='\n') if div_cirurgiao_details else ""
                        texto_div = texto_div.replace('\n', ' ').strip()
                        
                    else:
                        print("Div não encontrada, tentando novamente")
                        sleep(1)
                        texto_div = div_cirurgiao_details.get_text(separator='\n') if div_cirurgiao_details else ""
                        texto_div = texto_div.replace('\n', ' ').strip()
                        

                    nome = soup.find('h3', class_='cirurgiao-nome')
                    text_nome = nome.get_text(strip=True) if nome else "Nome não encontrado"
                    try:
                        img = soup.find('img', class_='cirurgiao-5x6')
                    except:
                        link_img = "Não tem imagem"

                    if img:
                        link_img = img.get("src")
                    
                    else:
                        link_img = "Não tem imagem"
                    
                    padrao_cidade = re.compile(r'Cidade:\s*([\w\s]+(?:,\s*\w{2})?)')
                    padrao_gmail = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+')
                    padrao_telefone = re.compile(r'\(\d{2}\) \d{2} - \d+')
                    padrao_crm = re.compile(r'[\d.]+/[A-Z]+')
                    padrao_categoria = re.compile(r'categoria:\s*([A-Z]+)')
                    padrao_endereco = re.compile(r'Endereço:\s*([a-zA-Z].*?)(?=(?:\w+:|$))')
                    padrao_site = re.compile(r'Website?:\s*(\S+)')

                    cidades = padrao_cidade.findall(texto_div)
                    gmails = padrao_gmail.findall(texto_div)
                    telefones = padrao_telefone.findall(texto_div)
                    crms = padrao_crm.findall(texto_div)
                    categorias = padrao_categoria.findall(texto_div)
                    enderecos = padrao_endereco.findall(texto_div)
                    sites = padrao_site.findall(texto_div)
                    
                    cidade = "Não tem cidade"
                    site = "Não tem site"
                    email_1, email_2 = "Não tem email", "Não tem email"
                    telefone_1, telefone_2 = "Não tem telefone", "Não tem telefone"
                    crm, categoria = "Não tem CRM", "Não tem categoria"
                    endereco_1, endereco_2 = "Não tem endereco", "Não tem endereco"

                    if cidades:
                        cidade = ', '.join(cidades)

                    if gmails:
                        quant_email = len(gmails)
                        if quant_email >= 1:
                            email_1 = gmails[0]
                        if quant_email >= 2:
                            email_2 = gmails[1]

                    if telefones:
                        quant_telefone = len(telefones)
                        if quant_telefone >= 1:
                            telefone_1 = telefones[0]
                        if quant_telefone >= 2:
                            telefone_2 = telefones[1]

                    if crms:
                        crm = ', '.join(crms)

                    if categorias:
                        categoria = ', '.join(categorias)

                    if enderecos:
                        quant_endereco = len(enderecos)
                        if quant_endereco >= 1:
                            endereco_1 = ' '.join(enderecos[0].split())
                        if quant_endereco >= 2:
                            endereco_2 = ' '.join(enderecos[1].split())
                    
                    if sites:
                        site = ', '.join(sites)
                        print(site)

                    query = f"""
                        INSERT INTO (add aqui o nome da sua tabela) 
                        (nome, cidade, email1, email2, telefone1, telefone2, crm, categoria, endereco1, endereco2, linkFoto, linkSite) 
                        VALUES 
                        ("{text_nome}", "{cidade}", "{email_1}", "{email_2}", "{telefone_1}", "{telefone_2}",
                        "{crm}", "{categoria}", "{endereco_1}", "{endereco_2}", "{link_img}", "{site}")
                    """
                    cursor.execute(query)
                    conexao.commit()

                    print(f'Dados inseridos no DB, registro Nº: {contador_registro}')
                    contador_registro += 1  

                    link.send_keys(Keys.ESCAPE)
                    sleep(1)
                
                except:
                    print("Informações não encontradas")
                    link.send_keys(Keys.ESCAPE)
                    sleep(1)
            
            cursor.close()
            conexao.close()

            conexao = criar_conexao()
            cursor = conexao.cursor()

            try:
                proxima_pagina = driver.find_element(By.XPATH, "//a[contains(text(),' 				Próximos →')]")
                print("Botão encontrado")
                driver.execute_script("arguments[0].scrollIntoView(true);", proxima_pagina)
                sleep(1)
                proxima_pagina.click()
                sleep(3)
            
            except NoSuchElementException:
                print("Não tem botão")
                break

    try:
        driver.quit()
    except Exception as e:
        print(f"Erro ao fechar o driver: {e}")

    driver = iniciar_driver()
    sleep(1)
