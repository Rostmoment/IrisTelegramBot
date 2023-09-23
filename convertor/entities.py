class MessageEntity:
    def __init__(self, type, offset, length, url=None, user=None, language=None, custom_emoji_id=None):
        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user
        self.language = language
        self.custom_emoji_id = custom_emoji_id
def convertEntities(entities):

    output_list = []
    for entity in entities:
        output_list.append({
            "offset": entity.offset,
            "length": entity.length,
            "type": entity.type
        })

    return output_list
