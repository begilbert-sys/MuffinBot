from timeit import default_timer

# wrapper that times function execution. for debugging purposes
def timed(func):
    def wrap(*args, **kwargs):
        start = default_timer()
        
        result = func(*args, **kwargs)
        
        end = default_timer()
        print(f'"{func.__qualname__}" call speed: {end - start}')
        return result
    return wrap