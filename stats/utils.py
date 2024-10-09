from hashlib import sha256
def hashed_id(user_id: int) -> str:
    '''Return the sha256 hex digest representation of an integer'''
    return sha256(str(user_id).encode('utf-8')).hexdigest()