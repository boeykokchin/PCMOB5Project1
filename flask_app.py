
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity

import os
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir,"db.sqlite")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# JWT setup
app.config['SECRET_KEY'] = 'anything'

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and password == user.password:
        return user

def identity(payload):
    return User.query.filter_by(id=payload["identity"]).first()

jwt = JWT(app, authenticate, identity)

## Add model for BlogPost
class BlogPost(db.Model):
    # no need init!
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.String(400))

    def json(self):
        return {"id": self.id, "title": self.title, "content": self.content}

## Add model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def json(self):
        return {"id": self.id, "username": self.username, "password": self.password}

db.create_all()

@app.route('/whoami')
@jwt_required()
def whoami():
    return { 'username': current_identity.username }

@app.route('/create', methods=['POST'])
def createPost():
    json_data = request.get_json(force=True)
    title = json_data["title"]
    content = json_data["content"]
    post = BlogPost(title=title, content=content)
    db.session.add(post)
    db.session.commit()
    return post.json()

@app.route('/posts/<int:id>', methods=['GET', 'DELETE', 'PUT'])
def getPost(id):
    # find the post with the given id before deciding what to do with it
    post = BlogPost.query.get(id)

    if post is None:
        # return "Not found", 404
        return abort(404)

    if request.method == 'PUT':
        json_data = request.json # no need get_json(force=True) if the sender
                                 # sends as Content-Type: application/json

        # check if the key exists in the dictionary
        if 'title' in json_data:
            post.title = json_data['title']
        if 'content' in json_data:
            post.content = json_data['content']
        db.session.commit()

    if request.method == 'DELETE':
        db.session.delete(post)
        db.session.commit()
        return {"Message": "Post id " + str(id) + " has been deleted."}

    return post.json()

@app.route('/posts')
def getAllPosts():
    posts = BlogPost.query.all()
    json_posts = []
    for post in posts:
        json_posts.append(post.json())
    return jsonify(json_posts)
    ## Alternatively...
    # return jsonify([post.json() for post in posts])

@app.route('/newuser', methods=['POST'])
def newuser():
    json_data = request.get_json()
    username = json_data["username"]
    password = json_data["password"]
    users = User.query.all()
    for u in users:
        if username == u.username:
            return { "Error": "User already exists" }
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    return { "Success": "New user " + username + " created" }

@app.route('/users', methods=['POST'])
def users():
    users=User.query.all()
    return jsonify([user.json() for user in users])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return {'about': 'This is an api for a blog! GET / to read more.'}
    return render_template('index.html')

# app.run should not run in PythonAnyWhere
if __name__ == '__main__':
    app.run(debug=True)
