import requests
from bs4 import BeautifulSoup
import uuid
import boto3

def lambda_handler(event, context):
    url = "https://ds.iris.edu/latin_am/evlist.phtml?limit=20&new=1"
    response = requests.get(url)
    
    # Verificar si la solicitud fue exitosa
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    # Parsear la página HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')  # Busca la primera tabla en la página

    # Extraer datos de la tabla
    sismos = []
    for row in table.find_all('tr')[1:]:  # Saltar el encabezado de la tabla
        cols = row.find_all('td')
        if len(cols) >= 6:  # Asegúrate de que haya suficientes columnas
            sismo = {
                'fecha_hora': cols[0].text.strip(),
                'latitud': cols[1].text.strip(),
                'longitud': cols[2].text.strip(),
                'magnitud': cols[4].text.strip(),
                'profundidad': cols[5].text.strip(),
                'localidad': cols[6].text.strip()
            }
            sismos.append(sismo)

    # Conexión a DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrappingSismosNuevo')  # Nuevo nombre de la tabla

    # Limpiar la tabla de registros antiguos
    with table.batch_writer() as batch:
        for item in table.scan()['Items']:
            batch.delete_item(Key={'id': item['id']})

    # Insertar nuevos registros y construir la respuesta
    arrreturn = []
    for i, sismo in enumerate(sismos, start=1):
        sismo['id'] = str(uuid.uuid4())
        sismo['#'] = i
        arrreturn.append(sismo)
        table.put_item(Item=sismo)

    # Devolver los datos de los sismos en el cuerpo de la respuesta
    return {
        'statusCode': 200,
        'body': arrreturn
    }
