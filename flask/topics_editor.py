import os
import json
from flask import Flask, Response, make_response, request, session, render_template, send_from_directory, redirect, abort
from werkzeug import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__, static_url_path='')
app.secret_key = os.urandom(24)

TREE_BASE_FILENAME = 'topics.json'
DATA_DIR = 'data'
DATA_DIR_PATH = '../{}'.format(DATA_DIR)
TREE_FILENAME = '{}/{}'.format(DATA_DIR_PATH, TREE_BASE_FILENAME)
ALLOWED_EXTENSIONS = set(['json'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

app.config.update(
    DEBUG=True,
    UPLOAD_FOLDER=DATA_DIR_PATH,
)


login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    # pass
    def __init__(self , username , password , active=True):
        self.id = username
        self.username = username
        self.password = password
        self.active = active

    def get_id(self):
        return self.id

    def is_active(self):
        return self.active

    def get_auth_token(self):
        return make_secure_token(self.username , key=app.secret_key)


class UsersRepository:
    def __init__(self):
        self.users = dict()
        self.users_id_dict = dict()

    def save_user(self , user):
        self.users_id_dict.setdefault(user.id , user)
        self.users.setdefault(user.username , user)

    def get_user(self , username):
        return self.users.get(username)

    def get_user_by_id(self , userid):
        return self.users.get(userid)


users_repository = UsersRepository()


@login_manager.user_loader
def load_user(userid):
    return users_repository.get_user_by_id(userid)


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    password = request.form.get('password')
    registeredUser = users_repository.get_user(username)
    if registeredUser == None or registeredUser.password != password:
        return abort(401)

    registeredUser.is_authenticated = registeredUser.password == password
    return registeredUser

@app.route('/login' , methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        registeredUser = users_repository.get_user(username)
        if registeredUser != None and registeredUser.password == password:
            print('Logged in..')
            login_user(registeredUser)
            return redirect('/web/index.html')
        else:
            return abort(401)
    else:
        return Response('''
            <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.13/semantic.min.css">
            <div class="ui middle aligned centered padded grid">
                <br/>
                <div class="ui segment">
                    <form action="" method="post">
                        <div class="ui header">Login</div>
                        <p><input type="email" name=username placeholder="Email" required></p>
                        <p><input type="password" name="password" placeholder="Password" required></p>
                        <p><button class="ui primary button" type="submit">Login</button></p>
                    </form>
                </div>
            </div>
        ''')


@app.route('/register' , methods = ['GET' , 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username , password)
        users_repository.save_user(new_user)
        return Response('''
            Registered Successfully. Please <a href="/login">login</a>
        ''')
    else:
        return Response('''
            <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.13/semantic.min.css">
            <div class="ui middle aligned centered padded grid">
                <br/>
                <div class="ui segment">
                    <form action="" method="post">
                        <div class="ui header">Sign up</div>
                        <p><input type="email" name=username placeholder="Email" required></p>
                        <p><input type="password" name="password" placeholder="Password" required></p>
                        <p><button class="ui primary button" type="submit">Register</button></p>
                    </form>
                </div>
            </div>
        ''')


@app.errorhandler(401)
def page_not_found(e):
    return Response('''
        <h3>Unauthorized</h3><br/>Please <a href="/register">Register</a> | <a href="/login">Login</a>
    ''')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Logged out'


@app.route('/tree', methods=['GET', 'POST'])
@login_required
def tree():
    if request.method == 'POST':
       content = request.data
       with open(TREE_FILENAME, 'w') as tree_file:
           tree_file.write(content)
       return "saved."
    else:
       with open(TREE_FILENAME, 'r') as tree_file:
           content = tree_file.read()
       return content


@app.route('/tree/file', methods=['GET', 'POST'])
@login_required
def download_tree_file():
    if request.method == 'POST':
        file = request.files['topics.json']
        if file and allowed_file(file.filename):
            filename = werkzeug.secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], TREE_FILENAME))
            return redirect('/web/index.html')
    else:
       with open(TREE_FILENAME, 'r') as tree_file:
               content = tree_file.read()
       response = make_response(content)
       response.headers["Content-Type"] = "application/json"
       response.headers["Content-Disposition"] = "attachment; filename={}".format(TREE_BASE_FILENAME)
       return response


@app.route('/web/<path:path>')
@login_required
def send_web(path):
       return send_from_directory('..', path)


@app.route('/')
@login_required
def index():
       return redirect('/web/index.html')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return Response('''
        <h3>Unauthorized</h3><br/>Please <a href="/register">Register</a> | <a href="/login">Login</a>
    ''')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6003, debug =True)
