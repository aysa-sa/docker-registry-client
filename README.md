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

## Métodos

### catalog

```python
def catalog(self, exp_filter=None, items=None, **kwargs):
```

Retorna una lista con el catálogo de imágenes.

```python
>>> # retorna la lista completa de la imágenes.
>>> for x in Api(...).catalog():
>>>     print(x)
project/image
project1/image
project2/image
...

>>> # retorna una lista filtrada por el "namesapce" => "project".
>>> for x in Api(...).catalog(r'^project'):
>>>     print(x)
project/image
project/image1
project/image2
...

>>> # retorna una lista pagainada cada "2" items.
>>> for x in Api(...).catalog(items=2):
>>>     print(x)
project/image
project1/image
```

### tags

```python
def tags(self, name, exp_filter=None, items=None, **kwargs):
```

Retorna una lista con el catálogo de tags de una imagen.

```python
>>> # retorna la lista completa de tags de una imagen.
>>> for x in Api(...).tags('image'):
>>>     print(x)
dev
...

>>> # recorre todo el catálogo de imágenes y tags.
>>> api = Api(...)
>>> for x in api.catalog():
>>>     for y in api.tags(x):
>>>         print(x, y)
project/image dev
project/image ...
```

### digest

```python
def digest(self, name, reference, **kwargs):
```

Retorna el "Docker-Content-Digest" de una image.

### manifest

```python
def manifest(self, name, reference, fat=False, obj=False, **kwargs):
```

Retorna el "Manifest" de una image en formato "json" u "object".

```python
>>> # versión simple en formato "json"
>>> Api(...).manifest('project/image', 'dev')

>>> # versión completa en formato "json"
>>> Api(...).manifest('project/image', 'dev', True)

>>> # versión completa en formato "object"
>>> Api(...).manifest('project/image', 'dev', obj=True)
```

### put_tag

```python
def put_tag(self, name, reference, target, **kwargs):
```

Crea un alias de tag a partir de otro existente.

### delete_tag

```python
def delete_tag(self, name, reference, **kwargs):
```

Elimina un tag específico.

### get_manifest

```python
def get_manifest(self, name, reference, fat=False, **kwargs):
```

Retorna un objeto response con el manifiesto.

```python
>>> Api(...).get_manifest('project/image', 'dev')
<Response [200]>

>>> Api(...).get_manifest('project/image', 'dev').json()
{'schemaVersion': 2, 'mediaType': 'application/vnd.docker...
```

### put_manifest

```python
def put_manifest(self, name, reference, manifest, **kwargs):
```

Crea un manifiesto específico.

### delete_manifest

```python
def delete_manifest(self, name, reference, **kwargs):
```

Elimina un manifiesto específico.

## Ejemplo

Recorremos el catálogo de repositorios que provee la registry `localhost:5000`.

```javascript
// GET http://localhost:5000/v2/_catalog
{
  "repositories": [
    "repository1/image1",  
    "repository1/image2",
    "repository2/image1",
    "repository3/image2"
  ]
}
```

Mediante la librería:

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

## Utils

### get_registry

```python
def get_registry(value):
```

Retorna el dominio(:puerto) de la registry.

```
ex: aysa.ad:5000/namespace/sub_namespace/image:tag
    => aysa.ad:5000
```

### get_repository

```python
def get_repository(value):
```

Retorna el nombre del repositorio.

```
ex: aysa.ad:5000/namespace/sub_namespace/image:tag
    => namespace/sub_namespace/image
```

### get_namespace

```python
def get_namespace(value):
```

Retorna el nombre del espacio.

```
ex: aysa.ad:5000/namespace/sub_namespace/image:tag
    => namespace/sub_namespace
```

### get_image

```python
def get_image(value):
```

Retorna el nombre de la imagen.

```
ex: aysa.ad:5000/namespace/sub_namespace/image:tag
    => image
```

### get_tag

```python
def get_tag(value):
```

Retorna el nombre del tag.

```
ex: aysa.ad:5000/namespace/sub_namespace/image:tag
    => tag
```

### get_parts

```python
def get_parts(value):
```

Retorna un diccionario con todas las partes que conforman el string.

Formato del string: `{url:port}/{namespace}/{repository}:{tag}`

```python
return {
    'registry': get_registry(value).rstrip('/'),
    'repository': get_repository(value),
    'namespace': get_namespace(value),
    'image': get_image(value),
    'tag': get_tag(value),
}
```


