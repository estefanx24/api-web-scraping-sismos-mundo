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
    table = soup.find('table')  # Buscar la tabla de sismos en la página

    # Extraer y ordenar los datos de la tabla
    array = []
    for row in table.find_all('tr')[1:]:  # Saltar el encabezado de la tabla
        cols = row.find_all('td')
        if len(cols) >= 6:  # Asegurarse de que haya suficientes columnas
            fecha_hora = cols[0].text.strip()
            latitud = cols[1].text.strip()
            longitud = cols[2].text.strip()
            magnitud = cols[3].text.strip()
            profundidad = cols[4].text.strip()
            localidad = cols[5].text.strip()
            
            # Almacenar el registro en el array con la fecha como clave
            array.append((fecha_hora, {
                'fecha_hora': fecha_hora,
                'latitud': latitud,
                'longitud': longitud,
                'magnitud': magnitud,
                'profundidad': profundidad,
                'localidad': localidad
            }))
    
    # Ordenar los registros por fecha/hora (si es necesario) y seleccionar los más recientes
    array.sort(key=lambda x: x[0], reverse=True)
    arr = [record[1] for record in array[:10]]  # Obtener solo los primeros 10 registros ordenados

    # Configuración de DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrappingSismosNuevo')  # Nuevo nombre de la tabla

    # Limpiar la tabla de registros antiguos
    with table.batch_writer() as batch:
        for item in table.scan()['Items']:
            batch.delete_item(Key={'id': item['id']})

    # Insertar nuevos registros en DynamoDB y construir el retorno
    arrreturn = []
    for i, data in enumerate(arr, start=1):
        data['#'] = i
        data['id'] = str(uuid.uuid4())
        arrreturn.append(data)
        table.put_item(Item=data)

    # Devolver los datos de los sismos en el cuerpo de la respuesta
    return {
        'statusCode': 200,
        'body': arrreturn
    }
