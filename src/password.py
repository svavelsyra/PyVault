class Password():
    def __init__(self, system='', username='', password='', notes=''):
        self.system = system
        self.username = username
        self.password = password
        self.notes = notes

    @staticmethod        
    def generate_password(password_type='alpha', n=10):
        alphabets = {'alpha': (string.ascii_letters, 'isupper', 'islower'),
                     'alphanum': (string.ascii_letters + string.digits, 'isupper', 'islower','isdigit'),
                     'alphanumspecial': (string.ascii_letters + string.digits + '!"#¤%&/()=?', 'isupper', 'islower','isdigit'),
                     'mobilealpha': (string.ascii_lowercase, 'islower'),
                     'mobilealphanum': (string.ascii_lowercase, 'islower'),
                     'mobilealphanumspecial': (string.ascii_lowercase, 'islower'),}
        if not password_type in alphabets:
            raise KeyError(f'Password type has to be one of the following: {", ".join(alphabets.keys())} it is "{password_type}".')
        while True:
            alphabet = alphabets[password_type][0]
            password = random.choices(alphabet, k=n)
            if password_type.startswith('mobile'):
                password[0] = password[0].upper()
            if 'mobilealphanum' in password_type :
                password[-2] = random.choise(string.digits)
            if password_type == 'mobilealphanumspecial':
                password[-1] = random.choise('!"#¤%&/()=?')
                
            for test in alphabets[password_type][1:]:
                if not [c for c in password if getattr(c, test)()]:
                    break
            else:
                if password_type == 'alphanumspecial':
                    if not [c for c in password if not c.isalpha()]:
                        continue
                break
        return ''.join(password)
