# Author: Alejandro M. BERNARDIS
# Email: alejandro.bernardis@gmail.com
# Created: 2019/11/20 09:30
# ~

import re
import requests
import logging
from requests.auth import HTTPBasicAuth
from http import HTTPStatus
from urllib import parse

log = logging.getLogger(__name__)

TAG_SEP = ':'
REPO_SEP = '/'
MANIFEST_VERSION = 'v2'

MEDIA_TYPES = {
    'v1': 'application/vnd.docker.distribution.manifest.v1+json',
    'v2': 'application/vnd.docker.distribution.manifest.v2+json',
    'v2f': 'application/vnd.docker.distribution.manifest.list.v2+json'
}

rx_schema = re.compile(r'^('
                       r'localhost|'
                       r'127\.0\.0\.1|'
                       r'[a-z0-9]([\w\-\.]*)\.local(?:host)?'
                       r')(?::\d{1,5})?$', re.I)
rx_registry = re.compile(r'^[a-z0-9]([\w\-\.]*)(?::\d{1,5})?$', re.I)
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
    _methods_supported = None

    def __init__(self, client):
        self.__client = client

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
        return self.cli.request(method, self.url, *args, **kwargs)

    def json(self, method, *args, **kwargs):
        return self.request(method, *args, **kwargs).json()


class IterEntity(Entity):
    _response_key = None
    _response_data = None

    def __init__(self, client, items=None):
        super().__init__(client)
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
    def params(self):
        return self.__params

    def set_params(self, values=None):
        if self.__items is None:
            self.__params = {}
        elif self.__params is None:
            self.__params = {'n': self.__items}
        values and self.__params.update(values)

    def test(self, *args, **kwargs):
        response = self.request('GET', params=self.params, *args, **kwargs)
        body = response.json()

        if self.key not in body:
            raise RegistryError('La clave "{}" no se encuentra dentro de la '
                                'respuesta.'.format(self.key))

        for item in body[self.key]:
            yield item

        link = response.headers.get('Link', None)

        if link is not None:
            link = link.partition(';')[0].rstrip('>')
            link = dict(parse.parse_qsl(parse.urlsplit(link).query))
            self.set_params(link)
            yield from self.test(*args, **kwargs)


class CatalogEntity(IterEntity):
    _url = '/_catalog'
    _response_key = 'repositories'
    _methods_supported = 'GET'
