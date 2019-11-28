# AySA / Docker Registry Api Client (v2019.11.22)

Cliente para la API v2 de Docker Registry.


> **WARNING!**
> Está pensado para implementar en capas de desarrollo, no para uso productivo.

## Instalación

Se requiere la versión de `python` **>=3.6**, en adelante.

### Con entorno virtual

```bash
# creamos el entorno virtual
> virtualenv --python=python37 docker-registry-client

# ingresamos al directorio del entorno
> cd docker-registry-client

# iniciamos el entorno
> source ./bin/activate

# instalamos dentro del entorno
> pip install https://github.com/aysa-sa/docker-registry-client/archive/2019.11.22.zip
```

### Sin entorno virtual

```bash
# Instalar
> pip install https://github.com/aysa-sa/docker-registry-client/archive/2019.11.22.zip

# Actualizar
> pip install https://github.com/aysa-sa/docker-registry-client/archive/2019.11.22.zip --upgrade
```

### Desde el código fuente

```bash
# clonamos el repositorio
> git clone https://github.com/aysa-sa/docker-registry-client.git --branch 2019.11.22 --single-branch 

# ingresamos al directorio del repositorio
> cd docker-registry-client

# instalamos
> python setup.py install
```

# Desarrollo

## Repositorio

```bash
# clonación
> git clone https://github.com/aysa-sa/docker-registry-client.git

# acceso al proyecto
> cd docker-registry-client
```

## Dependencias

Las dependencias se encuentran definidas en el archivo `Pipfile`, para la gestión de las mismas es requerido tener instalado `pipenv`, visitar [**site**](https://pipenv.readthedocs.io/).

### Pipenv

* Documentación: [**usage**](https://pipenv.readthedocs.io/en/latest/#pipenv-usage).
* Instalación: `pip install pipenv`.

#### Instalación de las dependencias:

```bash
> pipenv install
```

#### Iniciar el Shell:

```bash
> pipenv shell
```

#### Crear el archivo `requirements.txt`

```bash
> pipenv lock --requirements > requirements.txt
```


## Ejemplo

Recorremos el catálogo de imagágenes y sus respectivos tags:

```python
from aysa.docker.registry import Api, Image

# creamos una instancia de la api...
api = Api('localhost:5000', username='guest', password='guest')

# listamos todo el catálogo con sus respectivos tags...
for x in api.catalog():
    for y in api.tags(x):
        i = Image('{}:{}'.format(x, y))
        print(i)

# Output:
# repository1/image1:tag
# repository1/image2:tag
# repository2/image1:tag
# ...

# listamos sólo el repositorio "repository2"... 
for x in api.catalog('^repository2'):
    for y in api.tags(x):
        i = Image('{}:{}'.format(x, y))
        print(i)

# Output:
# repository2/image1:tag
# ...
```