import os
from flask import Flask, request, send_from_directory
import json
import numpy as np
from PIL import Image
import base64
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

# app.config['MYSQL_HOST'] = 'database-gallerys.cfm6weouifji.us-east-1.rds.amazonaws.com' 
# app.config['MYSQL_USER'] = 'admin' 
# app.config['MYSQL_PASSWORD'] = 'ErHFvr3MYT52tM5E5wF4' 
# app.config['MYSQL_DB'] = 'galeria'

app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root2'
app.config['MYSQL_DB'] = 'galeria'
app.config['MYSQL_DATABASE_PORT'] = 3306

# mysql = MySQL(app)

# Las rutas publicas para acceder a archivos publicos, despues del /public el usuario puede buscar cualquier direccion
# Si existe, se le devuelve el archivo solicitado, sirve para acceder a las imagenes.
@app.route("/public/<path:path>")
def send_images(path):
    return send_from_directory('public', path)

# Prueba de que el servidor esta en linea
@app.route("/", methods=["GET"])
def index_route():
    return json.dumps({
        "status": 200,
        "message": "Pokemones padres en acción"
    })

@app.route("/image", methods=["POST"])
def image_route():
    # Obtener imagen en base 64 y la pasamos a imagen (como archivo o conjunto de bytes)
    image64 = request.form.get("image").split(",")[1]
    image = readb64(image64)

    # Aplicar las transformaciones a la imagen en color
    imagen_ecualizada = ecualizar_histograma_color(image)
    imagen_invertida = invertir_imagen_color(image)

    # Ajuste gamma con un valor de gamma de ejemplo
    gamma = 3
    imagen_gamma = ajuste_gamma_color(image, gamma)

    #Suavizado de imagenenes
    imagen_suavizada=suvizado_imagen(image,mascara_media)

    #recolorizacion de imagenes

    # Llamara a la función escala de grises
    imagen_gris = convertir_a_escala_de_grises_recoloracion(image)
    imagen_recolorizada = convertir_a_escala_de_color(imagen_gris)

    #Bordes
    imagen_bordes=suvizado_imagen(image,sobelX)

    # Codificar las imágenes de salida a base64
    imagen_ecualizada_base64 = codificar_base64(imagen_ecualizada)
    imagen_invertida_base64 = codificar_base64(imagen_invertida)
    imagen_gamma_base64 = codificar_base64(imagen_gamma)
    imagen_suavizada_base64 = codificar_base64(Image.fromarray(imagen_suavizada))
    imagen_bordes_base64 = codificar_base64(Image.fromarray(imagen_bordes))
    imagen_recolorizada_base64 = codificar_base64(imagen_recolorizada)

    return json.dumps({
        'statusCode': 200,
        'imagen_ecualizada': imagen_ecualizada_base64,
        'imagen_invertida': imagen_invertida_base64,
        'imagen_gamma': imagen_gamma_base64,
        'imagen_colorizada': imagen_recolorizada_base64,
        'imagen_suavizada':imagen_suavizada_base64,
        'imagen_bordes':imagen_bordes_base64
    })

@app.route("/create_gallery", methods=["PUT"])
def create_gallery():
    try:
        # Obtenemos la informacion de la galeria desde el formulario
        galeria = request.form.get("galeria")
        descripcion = request.form.get("descripcion")
        titulos = request.form.get("titulos")
        imagenes = request.form.get("imagenes")
        descripciones_extra = request.form.get("descripciones_extra")

        # Los arreglos llegan como cadena, se convierten a json
        titulos = json.loads(titulos)
        imagenes = json.loads(imagenes)
        descripciones_extra = json.loads(descripciones_extra)

        # Declaramos el arreglo donde se almacenaran las imagenes dentro del json
        imagenes_obj_array = []

        # Recorremos los arreglos y creamos la imagen en la carpeta public/imagenes
        # Luego anexamos los datos de las imagenes al arreglo
        # En caso de que la creacion del archivo falle, no se hará el registro
        for i in range(len(titulos)):
            imagenes_obj = {}
            write_image(imagenes[i], titulos[i], i)
            imagenes_obj["image"] = f"/public/imagenes/{titulos[i]}_{i}.png"
            imagenes_obj["image_name"] = titulos[i]
            imagenes_obj["image_description"] = descripciones_extra[i]
            imagenes_obj_array.append(imagenes_obj)

        # Obtenemos el archivo json
        data = read_from_json()

        # Anexamos al final del arreglo nuestro mas reciente objeto, su id corresponde al tamaño del arreglo al momento de crearse
        data['galleries'].append({
            "idgallery": len(data['galleries']),
            "name_gallery": galeria,
            "gallery_description": descripcion,
            "images": imagenes_obj_array
        })

        # Reescribimos el json
        write_on_json(data)

        # Termina el proceso con mensaje de conclusion exitosa
        return json.dumps({
            "statusCode": 200,
            "message": "Galeria creada exitosamente"
        })
    except Exception as error:
        print(error)
        return json.dumps({
            "statusCode": 500,
            "message": "Error cargando la galeria"
        })

@app.route("/get_galleries", methods=["GET"])
def get_galleries():
    try:
        # Leemos el archivo json
        data = read_from_json()

        # Retornamos el valor que se encuentra dentro del arreglo de galerias
        return json.dumps({
            "statusCode": 200,
            "message": "Data successfully",
            "data": data["galleries"]
        })
    except Exception as e:
        print(e)
        return json.dumps({
            "statusCode": 500,
            "message": "Error " + str(e),
            "data": []
        })

# Ahora se borra con la posicion del arreglo, no por un id, por lo que el id será dinamico ya que depende de donde se guarde
@app.route("/delete_gallery", methods=["POST"])
def delete_gallery():
    idgaleria = request.form.get("idgallery")
    # convertimos el id a int porque si no la funcion pop no hace lo que debe
    idgaleria = int(idgaleria)
    try:
        # Obtenemos el valor actual del json
        data = read_from_json()
        index =-1
        for i in range (len(data["galleries"])):
            if data["galleries"][i]["idgallery"]==idgaleria:
                index=i
            break
        # Eliminamos el valor en la posicion del id
        data['galleries'].pop(index)

        # Reescribimos el json ya sin el objeto eliminado
        write_on_json(data)

        return json.dumps({
            "statusCode": 200,
            "message": "Data successfully",
            "data": data['galleries']
        })
    except Exception as e:
        print(e)
        return json.dumps({
            "statusCode": 500,
            "message": "Error " + str(e),
            "data": []
        })

# Funcion para obtener la data del json
def read_from_json():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "galleries.json")
    data = json.load(open(json_url))
    return data

def write_on_json(data):
    with open("galleries.json", "w") as f:
        json.dump(data, f)

def write_image(base_64_string, nombre, index):
    with open(f"public/imagenes/{nombre.strip()}_{index}.png", "wb") as fh:
        fh.write(base64.decodebytes(base_64_string.split(",")[1].encode()))

def readb64(base64_string):
    decoded_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(decoded_data))
    return image

def invertir_imagen_color(imagen):
    np_image = np.array(imagen)
    np_invertida = 255 - np_image
    return Image.fromarray(np_invertida)

def ajuste_gamma_color(imagen, gamma):
    np_image = np.array(imagen) / 255.0
    np_gamma_corrected = np.power(np_image, gamma) * 255.0
    return Image.fromarray(np_gamma_corrected.astype(np.uint8))

def ecualizar_histograma_color(imagen):
    np_image = np.array(imagen)
    if len(np_image.shape) == 2:  # Imagen en escala de grises
        np_eq = ecualizar_histograma_gris(np_image)
    else:  # Imagen a color
        np_eq = np.zeros_like(np_image)
        for channel in range(np_image.shape[2]):
            np_eq[:, :, channel] = ecualizar_histograma_gris(np_image[:, :, channel])
    return Image.fromarray(np_eq)

def ecualizar_histograma_gris(channel):
    # Calcular el histograma
    hist, bins = np.histogram(channel.flatten(), 256, [0, 256])
    
    # Calcular el histograma acumulativo
    cdf = hist.cumsum()
    
    # Normalizar el histograma acumulativo
    cdf_normalized = cdf * hist.max() / cdf.max()
    
    # Aplicar la transformación de ecualización
    cdf_m = np.ma.masked_equal(cdf, 0)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    cdf = np.ma.filled(cdf_m, 0).astype('uint8')
    
    # Mapear los valores del canal original a los valores ecualizados
    np_eq_channel = cdf[channel]
    return np_eq_channel

#def suavizado_imagen(imagen)
def suvizado_imagen(imagen, mascara):
    # Convertir la imagen a un array de numpy si es un objeto PIL
    if isinstance(imagen, Image.Image):
        np_image = np.array(imagen)
    else:
        np_image = np.array(imagen)
    altura, ancho, canales = np_image.shape
    m, n = mascara.shape
    centro = m // 2
    # Padding de la imagen
    padded_image = np.pad(np_image.astype(float),
                          ((centro, centro), (centro, centro), (0, 0)),
                          mode='constant')
    resultado = np.zeros_like(np_image, dtype=float)
    # Realizar la convolución
    for i in range(m):
        for j in range(n):
            resultado += padded_image[i:i + altura, j:j + ancho] * mascara[i, j]

    return np.clip(resultado, 0, 255).astype(np.uint8)

# Construir la máscara de media
mascara_media = np.ones((11, 11)) / 121  # Filtro de media

#Recolorizacion de imagenes

# Convertir a escala de grises
def convertir_a_escala_de_grises_recoloracion(imagen):
    # Convertir la imagen a una matriz numpy
    array_imagen = np.array(imagen)

    # Aplicar la fórmula precisa para convertir a escala de grises
    imagen_gris = 0.21 * array_imagen[:, :, 0] + 0.72 * array_imagen[:, :, 1] + 0.07 * array_imagen[:, :, 2]

    # Convertir la matriz resultante a formato de imagen
    imagen_gris = Image.fromarray(imagen_gris.astype('uint8'))

    return imagen_gris

def ajustar_tonos_rojizos_a_verde(r, g, b, factor_ajuste=0.3):
    # Ajustar el componente verde si el componente rojo es dominante
    if r > g and r > b:
        g = min(255, g + int(factor_ajuste * r))
    return r, g, b

def convertir_a_escala_de_color(imagen_gris):
    # Convertir la imagen en escala de grises a una matriz numpy
    array_gris = np.array(imagen_gris)

    # Valor central para la transformación
    valor_central = 128

    # Aplicar la transformación de escala de grises a escala de color
    imagen_color = np.zeros((array_gris.shape[0], array_gris.shape[1], 3), dtype=np.uint8)
    for i in range(array_gris.shape[0]):
        for j in range(array_gris.shape[1]):
            valor_pixel = array_gris[i, j]
            if valor_pixel < valor_central:
                r = min(255, max(0, int(255 * valor_pixel / valor_central)))
                g = min(255, max(0, int(100 * valor_pixel / valor_central)))
                b = min(255, max(0, int(100 * valor_pixel / valor_central)))
            else:
                r = min(255, max(0, int(255)))
                g = min(255, max(0, int(100 + (155 * (valor_pixel - valor_central) / valor_central))))
                b = min(255, max(0, int(100 + (155 * (valor_pixel - valor_central) / valor_central))))

            # Ajustar tonos rojizos a verde
            r, g, b = ajustar_tonos_rojizos_a_verde(r, g, b)

            imagen_color[i, j] = [r, g, b]

    return Image.fromarray(imagen_color)

#Bordes

# Construcción de la máscara sobelX
sobelX = np.array([[-1, 0, 1], 
                   [-2, 0, 2], 
                   [-1, 0, 1]])

def codificar_base64(imagen):
    buffered = BytesIO()
    imagen.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
