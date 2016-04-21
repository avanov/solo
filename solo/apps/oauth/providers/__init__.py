class FacebookProvider:
    def __init__(self, name, consumer_key, consumer_secret, scope):
        self.name = name
        self.type = 'facebook'
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.scope = scope
        self.display = 'page'
