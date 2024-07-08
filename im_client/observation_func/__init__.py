observation_registry = {}


def register_observation(name):
    def decorator(func):
        observation_registry[name] = func
        return func

    return decorator


from .rocobench import get_observation


@register_observation("dummy")
def get_observation(*args, **kwargs):
    return ""
