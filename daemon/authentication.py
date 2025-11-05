class Authentication():
    __attrs = [
            "auth_table"
    ]

    def __init__(self, filepath="static/database/auth_table.txt"):
        file = open(filepath, "r")
        content = file.read()
        lines = content.split("\r\n")

        for line in lines:
            split_line = line.split("=")
            if(len(split_line == 2)):
                [key, value] = line.split("=") 
                auth_table[key] = value

    def authenticate(self, body):
        body_arr = body.split('&')
        username = ''
        password = ''

        for line in body_arr:
            split_line = line.split('=')
            if len(split_line) == 2:
                [username, password] = split_line 

        if(auth_table.get(body_dict["username"], '') == body_dict["password"]):
            return True
        else: 
            return False

