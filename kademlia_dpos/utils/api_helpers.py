from functools import wraps
from flask import jsonify

def require_consensus(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from kademlia_dpos.api import consensus
        
        if consensus is None:
            return jsonify({
                'error': '節點正在初始化，請稍後重試',
                'status': 'initializing'
            }), 503
        return f(*args, **kwargs)
    return decorated_function
