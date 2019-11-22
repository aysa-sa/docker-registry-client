# Author: Alejandro M. BERNARDIS
# Email: alejandro.bernardis@gmail.com
# Created: 2019/11/20 09:30
# ~

import re
import json
import requests
from requests.auth import HTTPBasicAuth
from http import HTTPStatus
from urllib import parse

TAG_SEP = ':'
REPO_SEP = '/'

MEDIA_TYPES = {
    'v1': 'application/vnd.docker.distribution.manifest.v1+json',
    'v2': 'application/vnd.docker.distribution.manifest.v2+json',
    'v2f': 'application/vnd.docker.distribution.manifest.list.v2+json'
}

rx_schema = re.compile(r'^('
                       r'localhost|'
                       r'127\.0\.0\.1|'
                       r'[a-z0-9]([\w\-.]*)\.local(?:host)?'
                       r')(?::\d{1,5})?$', re.I)

rx_registry = re.compile(r'^[a-z0-9]([\w\-.]*)(?::\d{1,5})?/', re.I)

rx_repository = re.compile(r'^[a-z0-9][\w\-]*(?:[\w\-/]+)'
                           r'(?::[a-z0-9][\w\-./]*)?$', re.I)


class RegistryError(Exception):
    pass


def schema(endpoint):
    return 'http' if rx_schema.match(endpoint) else 'https'


class Registry:
    def __init__(self, host, insecure=False, verify=True, username=None,
                 password=None, **kwargs):
        self.__host = host
        self.__insecure = insecure
        self.__verify = verify if insecure is False else False
        self.__schema = schema(host) if insecure is False else 'http'
        self.__username = username
        self.__password = password
        self.__options = kwargs

    @property
    def host(self):
        return self.__host

    @property
    def insecure(self):
        return self.__insecure

    @property
    def verify(self):
        return self.__verify

    @property
    def username(self):
        return self.__username

    @property
    def schema(self):
        return self.__schema

    @property
    def password(self):
        return self.__password

    @property
    def credentials(self):
        return all([self.username, self.password])

    def url(self, value=None):
        return '{}://{}/v2{}'.format(self.schema, self.host, value or '')

    def session(self, headers=None, timeout=25):
        s = requests.Session()
        if self.credentials is not None:
            s.auth = HTTPBasicAuth(self.username, self.password)
        s.headers.update(headers or {})
        s.headers['User-Agent'] = 'AySA-Docker-Registry-Api-Client'
        s.verify = self.verify
        s.timeout = timeout
        return s

    def request(self, method, url, *args, **kwargs):
        headers = kwargs.pop('headers', {})
        with self.session(headers) as req:
            response = req.request(method, self.url(url), *args, **kwargs)
            try:
                response.raise_for_status()
            except requests.HTTPError:
                data = response.json()
                if 'errors' in data:
                    error = data['errors'][0]
                    raise RegistryError('{code}: {message}'.format(**error))
            return response

    def status_code(self, method, url, *args, **kwargs):
        return self.request(method, url, *args, **kwargs).status_code

    def ping(self):
        try:
            return self.status_code('GET', '') == HTTPStatus.OK
        except Exception:
            return False


class Entity:
    _url = None
    _url_template = None
    _headers = None
    _methods_supported = None

    def __init__(self, client, set_url=None, **kwargs):
        self.__client = client
        if set_url is not None:
            self.set_url(**set_url)

    @property
    def cli(self):
        return self.__client

    @property
    def url(self):
        return self._url

    @property
    def url_template(self):
        return self._url_template

    @property
    def headers(self):
        return self._headers

    @property
    def methods_supported(self):
        return self._methods_supported or []

    def set_url(self, **kwargs):
        if self.url_template is None:
            raise RegistryError('Método "set_url" no está soportado '
                                'para la entidad: "{}".'
                                .format(self.__class__.__name__))
        self._url = self.url_template.format(**kwargs)

    def request(self, method, *args, **kwargs):
        method = method.upper()
        if method not in self.methods_supported:
            raise RegistryError('Método "{}" no soportado para "{}".'
                                .format(method, self.url))
        if self.headers:
            kwargs['headers'] = self.headers
        return self.cli.request(method, self.url, *args, **kwargs)

    def json(self, method, *args, **kwargs):
        return self.request(method, *args, **kwargs).json()


class IterEntity(Entity):
    _response_key = None
    _response_data = None

    def __init__(self, client, exp_filter=None, items=None, **kwargs):
        super().__init__(client, **kwargs)
        if isinstance(exp_filter, str):
            exp_filter = re.compile(exp_filter, re.I)
        self.__exp_filter = exp_filter
        self.__items = items
        self.__params = None
        self.set_params()

    @property
    def key(self):
        return self._response_key

    @property
    def data(self):
        return self._response_data

    @property
    def exp_filter(self):
        return self.__exp_filter

    @property
    def params(self):
        return self.__params

    def set_params(self, values=None):
        if self.__items is None:
            self.__params = {}
        elif self.__params is None:
            self.__params = {'n': self.__items}
        values and self.__params.update(values)

    def next(self, *args, **kwargs):
        response = self.request('GET', params=self.params, *args, **kwargs)
        body = response.json()
        if self.key not in body:
            raise RegistryError('La clave "{}" no se encuentra dentro de la '
                                'respuesta.'.format(self.key))
        for item in body[self.key]:
            if self.exp_filter and not self.exp_filter.match(item):
                continue
            yield item
        link = response.headers.get('Link', None)
        if link is not None:
            link = link.partition(';')[0].rstrip('>')
            link = dict(parse.parse_qsl(parse.urlsplit(link).query))
            self.set_params(link)
            yield from self.next(*args, **kwargs)

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self.next()


class CatalogEntity(IterEntity):
    _url = '/_catalog'
    _response_key = 'repositories'
    _methods_supported = 'GET',


class TagsEntity(IterEntity):
    _url_template = '/{name}/tags/list'
    _response_key = 'tags'
    _methods_supported = 'GET',

    def __init__(self, client, name, exp_filter=None, items=None, **kwargs):
        kwargs['set_url'] = {'name': name}
        super().__init__(client, exp_filter, items, **kwargs)


class ManifestEntity(Entity):
    _url_template = '/{name}/manifests/{reference}'
    _methods_supported = 'GET', 'PUT', 'DELETE'
    _headers = {'Accept': MEDIA_TYPES['v2']}

    def __init__(self, client, name, reference, **kwargs):
        kwargs['set_url'] = {'name': name, 'reference': reference}
        super().__init__(client, **kwargs)


class FatManifestEntity(ManifestEntity):
    _methods_supported = 'GET',
    _headers = {'Accept': MEDIA_TYPES['v2f']}


def _remove_registry(value):
    registry = get_registry(value)
    if registry is not None:
        value = value.replace(registry, '')
    return value


def get_registry(value):
    """
    Retorna el dominio(:puerto) de la registry.

    ex: aysa.ad:5000/namespace/sub_namespace/image:tag
        => aysa.ad:5000
    """
    registry = rx_registry.match(value)
    if registry is not None:
        return registry.group()
    return None


def get_repository(value):
    """
    Retorna el nombre del repositorio.

    ex: aysa.ad:5000/namespace/sub_namespace/image:tag
        => namespace/sub_namespace/image
    """
    return _remove_registry(value).rsplit(TAG_SEP, 1)[0]


def get_namespace(value):
    """
    Retorna el nombre del espacio.

    ex: aysa.ad:5000/namespace/sub_namespace/image:tag
        => namespace/sub_namespace
    """
    value = get_repository(value)
    if REPO_SEP not in value:
        return None
    return value.rsplit(REPO_SEP, 1)[0]


def get_image(value):
    """
    Retorna el nombre de la imagen.

    ex: aysa.ad:5000/namespace/sub_namespace/image:tag
        => image
    """
    return get_repository(value).rsplit(REPO_SEP, 1)[-1]


def get_tag(value):
    """
    Retorna el nombre del tag.

    ex: aysa.ad:5000/namespace/sub_namespace/image:tag
        => tag
    """
    value = _remove_registry(value)
    if TAG_SEP not in value:
        return None
    return value.rsplit(TAG_SEP, 1)[-1]


def get_parts(value):
    """Formato del string: {url:port}/{namespace}/{repository}:{tag}"""
    if not rx_repository.match(get_repository(value)):
        raise RegistryError('El endpoint "{}" está mal formateado.'
                            .format(value))
    return {
        'registry': get_registry(value).rstrip('/'),
        'repository': get_repository(value),
        'namespace': get_namespace(value),
        'image': get_image(value),
        'tag': get_tag(value),
    }


class Image:
    def __init__(self, string):
        self.__parts = get_parts(string)
        self.__raw = string

    @property
    def registry(self):
        return self.__parts['registry']

    @property
    def repository(self):
        return self.__parts['repository']

    @property
    def namespace(self):
        return self.__parts['namespace']

    @property
    def image(self):
        return self.__parts['image']

    @property
    def tag(self):
        return self.__parts['tag']

    @property
    def raw(self):
        return self.__raw

    @property
    def parts(self):
        return self.__parts

    @property
    def image_tag(self):
        return '{}:{}'.format(self.image, self.tag)

    @property
    def repository_tag(self):
        return '{}:{}'.format(self.repository, self.tag)

    def __str__(self):
        return self.raw

    def __repr__(self):
        return '<{registry} Namespace="{namespace}", Image="{image}", '\
               'Tag="{tag}">'\
               .format(**{k: v or '' for k, v in self.__parts.items()})

    def __lt__(self, other):
        return self.image < other.image

    def __gt__(self, other):
        return self.image > other.image


class Manifest:
    def __init__(self, raw):
        self._raw = raw
        self._history = None

    @property
    def name(self):
        return self._raw.get('name', None)

    @property
    def tag(self):
        return self._raw.get('tag', None)

    @property
    def layers(self):
        return self._raw.get('fsLayers', self._raw.get('layers', None))

    @property
    def history(self):
        try:
            if self._history is None:
                raw = self._raw['history'][0]['v1Compatibility']
                self._history = json.loads(raw)
            return self._history
        except Exception:
            return {}

    @property
    def created(self):
        return self.history.get('created', None)

    @property
    def schema(self):
        return self._raw.get('schemaVersion', None)


class Api(Registry):
    """
    Docker Registry Api Client

    >>> api = Api('localhost:5000', username='guest', password='guest')
    """

    def catalog(self, exp_filter=None, items=None, **kwargs):
        """
        Retorna la lista con el catálogo de imágenes.

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
        """
        return CatalogEntity(self, exp_filter, items, **kwargs)

    def tags(self, name, exp_filter=None, items=None, **kwargs):
        """
        Retorna la lista con el catálogo de tags de una imagen.

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
        """
        return TagsEntity(self, name, exp_filter, items, **kwargs)

    def digest(self, name, reference, **kwargs):
        """Retorna el "Docker-Content-Digest" de una image."""
        response = self.get_manifest(name, reference, **kwargs)
        return response.headers.get('Docker-Content-Digest', None)

    def manifest(self, name, reference, fat=False, obj=False, **kwargs):
        """
        Retorna el "Manifest" de una image en formato "json" u "object".

        >>> # versión simple en formato "json"
        >>> Api(...).manifest('project/image', 'dev')

        >>> # versión completa en formato "json"
        >>> Api(...).manifest('project/image', 'dev', True)

        >>> # versión completa en formato "object"
        >>> Api(...).manifest('project/image', 'dev', obj=True)
        """
        response = self.get_manifest(name, reference, fat, **kwargs).json()
        return Manifest(response) if obj is False else response

    def put_tag(self, name, reference, target, **kwargs):
        """Crea un alias de tag a partir de otro existente."""
        manifest = self.get_manifest(name, reference, **kwargs)
        return self.put_manifest(name, target, manifest, **kwargs)

    def delete_tag(self, name, reference, **kwargs):
        """Elimina un tag específico."""
        digest = self.digest(name, reference, **kwargs)
        return self.delete_manifest(name, digest, **kwargs)

    def get_manifest(self, name, reference, fat=False, **kwargs):
        """
        Retorna un objeto response con el manifiesto.

        >>> Api(...).get_manifest('project/image', 'dev')
        <Response [200]>

        >>> Api(...).get_manifest('project/image', 'dev').json()
        {'schemaVersion': 2, 'mediaType': 'application/vnd.docker...
        """
        return self._manifest(name, reference, fat, **kwargs)\
                   .request('GET', **kwargs)

    def put_manifest(self, name, reference, manifest, **kwargs):
        """Crea un manifiesto específico."""
        return self._manifest(name, reference, **kwargs) \
                   .request('PUT', json=manifest, **kwargs)

    def delete_manifest(self, name, reference, **kwargs):
        """Elimina un manifiesto específico."""
        return self._manifest(name, reference, **kwargs) \
                   .request('DELETE', **kwargs)

    def _manifest(self, name, reference, fat=False, **kwargs):
        obj = ManifestEntity if fat is False else FatManifestEntity
        return obj(self, name, reference, **kwargs)
