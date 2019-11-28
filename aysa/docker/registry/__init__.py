# Author: Alejandro M. BERNARDIS
# Email: alejandro.bernardis@gmail.com
# Created: 2019/11/22 14:16
# ~

try:
    from aysa.docker.registry.api import Api, Image, Manifest, get_parts, \
        get_registry, get_namespace, get_repository, get_image, get_tag

except ImportError:
    pass
