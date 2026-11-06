def get_or_load(cache, key, loader):
    value = cache.get(key)
    if not value:
        value = loader(key)
        cache[key] = value
    return value
