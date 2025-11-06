class Authentication():
    __attrs__ = [
            "auth_table"
    ]

    def __init__(self, filepath="static/database/auth_table.txt"):
        file = open(filepath, "r")
        content = file.read()
        lines = content.split("\n")
        self.auth_table = {}

        for line in lines:
            split_line = line.split(":")
            if(len(split_line) == 2):
                [key, value] = split_line
                self.auth_table[key] = value

        print(self.auth_table)

    def authenticate(self, body):
        body_arr = body.split('&')
        body_dict = {}

        for line in body_arr:
            split_line = line.split('=')
            if len(split_line) == 2:
                [key, value] = split_line 
                body_dict[key] = value

        username = body_dict["username"]
        password = body_dict["password"]
        print(username + ":" + password)
        if(self.auth_table.get(username, '') == password):
            return True
        else: 
            return False


if __name__ == "__main__":
    auth = Authentication("../static/database/auth_table.txt")

    auth.authenticate("username=admin&password=password")
